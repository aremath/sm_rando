from . import byte_ops

class Address(object):
    """Address Class that handles conversions
       this way we don't have to remember which 'kind' of address we have
       just which kind we want to use"""
    def __init__(self, addr, mode="pc"):
        if mode == "pc":
            self.from_pc(addr)
        elif mode == "snes":
            self.from_snes(addr)
        else:
            assert False, "Bad address mode: " + mode

    def __repr__(self):
        return hex(self.as_pc())

    def __gt__(self, other):
        return self.as_pc() > other.as_pc()

    def __eq__(self, other):
        return self.as_pc() == other.as_pc()

    def __add__(self, other):
        return Address(self.as_pc() + other.as_pc())

    # Hashable as its actual address
    def __hash__(self):
        return hash(self.pc_addr)

    def from_snes(self,addr):
        self.pc_addr = byte_ops.snes_to_pc(addr)

    def from_pc(self,addr):
        self.pc_addr = addr

    def as_pc(self):
        return self.pc_addr

    def as_snes(self):
        sn = byte_ops.pc_to_snes(self.pc_addr)
        return sn
    
    def as_snes_bytes(self, nbytes):
        assert (nbytes == 2 or nbytes == 3), "Can't produce a " + str(nbytes) + "-byte pointer!"
        sn = byte_ops.pc_to_snes(self.pc_addr)
        b = sn.to_bytes(3, byteorder='little')
        return b[:nbytes]
    
    def bank(self):
        return (byte_ops.pc_to_snes(self.pc_addr) & 0xff0000) >> 16

    def copy_increment(self,inc):
        ad = self.as_pc() + inc
        return Address(ad)

def mk_future(i):
    return FutureAddress(real_addr=Address(i))

class FutureAddress(object):
    """Represents an address which is currently unknown."""
    
    def __init__(self, name="", real_addr=None):
        self.name = name
        self.real_addr = real_addr

    def resolve(self, env):
        if self.real_addr is None:
            addr = env[self.name]
            if hasattr(addr, "as_pc"):
                self.real_addr = addr
                return addr
            elif hasattr(addr, "resolve"):
                addr = addr.resolve(env)
                self.real_addr = addr
                return addr
            else:
                assert isinstance(addr, int)
                return addr
        else:
            return self.real_addr

    def __add__(self, other):
        if hasattr(other, "resolve"):
            return FutureAddressOp(lambda x,y: x + y, self, other)
        else:
            assert False

    def __repr__(self):
        if self.real_addr is not None:
            return self.real_addr.__repr__()
        else:
            return "future({})".format(self.name)

class FutureAddressOp(object):
    """Represents a binary expression tree for FutureAddresses."""
    
    def __init__(self, op, fa1, fa2=None):
        self.op = op
        self.fa1 = fa1
        self.fa2 = fa2

    def resolve(self, env):
        assert self.fa1 is not None
        if self.fa2 is None:
            if self.op is None:
                return self.fa1.resolve(env)
            else:
                return self.op(self.fa1.resolve(env))
        else:
            a1 = self.fa1.resolve(env)
            a2 = self.fa2.resolve(env)
            return self.op(a1, a2)

    def __add__(self, other):
        if hasattr(other, "resolve"):
            return FutureAddressOp(lambda x, y: x+y, self, other)
        else:
            assert False

    def __repr__(self):
        f1 = self.fa1.__repr__()
        f2 = self.fa2.__repr__()
        return "futureop({}, {})".format(f1, f2)

#TODO: also verify bank of where we're being written?
class FutureAddressWrite(object):
    """Represents a place to fill an unknown pointer."""

    def __init__(self, ptr, place, size, bank=None):
        self.ptr = ptr
        self.place = place
        self.bank = bank
        self.size = size
        
    def fill(self, rom, env):
        place = self.place.resolve(env)
        addr  = self.ptr.resolve(env)
        if hasattr(addr, "as_snes_bytes"):
            #TODO: right now this does the format regardless of whether the assert fires. This is slow.
            # Sad assert doesn't go over multiple lines :(
            assertmsg = "Pointer's bank ({}) does not match expected bank ({})".format(addr.bank(), self.bank)
            assert self.bank is None or addr.bank() == self.bank, assertmsg
            rom.write_to_new(place, addr.as_snes_bytes(self.size))
        # If the address isn't an Address, then treat it as an int
        # Hack for being able to use literal numbers like for the scrolls ptr.
        else:
            b = addr.to_bytes(self.size, byteorder='little')
            rom.write_to_new(place, b)

    def __repr__(self):
        return "futurewrite({}, {})".format(self.ptr, self.place)

