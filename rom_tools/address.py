from . import byte_ops

class Address(object):
    """Address Class that handles conversions
       this way we don't have to remember which 'kind' of address we have
       just which kind we want to use"""
    def __init__(self, pc):
        self.from_pc(pc)

    def __repr__(self):
        return hex(self.as_pc())

    def __gt__(self, other):
        return self.as_pc() > other.as_pc()

    def __eq__(self, other):
        return self.as_pc() == other.as_pc()

    def __add__(self, other):
        return Address(self.as_pc() + other.as_pc())

    def from_snes(self,addr):
        byte_ops.assert_valid_snes(addr)
        self.pc_addr = byte_ops.snes_to_pc(addr)

    def from_pc(self,addr):
        self.pc_addr = addr

    def as_pc(self):
        return self.pc_addr

    def as_snes(self):
        sn = byte_ops.pc_to_snes(self.pc_addr)
        byte_ops.assert_valid_snes(sn)
        return sn
    
    def as_snes_bytes(self, nbytes):
        assert (nbytes == 2 or nbytes == 3), "Can't produce a " + str(nbytes) + "-byte pointer!"
        sn = byte_ops.pc_to_snes(self.pc_addr)
        b = int.to_bytes(sn, byteorder='little')
        return b[:nbytes]
    
    def bank(self)
        return byte_ops.pc_to_snes(self.pc_addr) & 0xff0000

    def copy_increment(self,inc):
        ad = self.as_pc() + inc
        new = Address()
        new.from_pc(ad)
        return new

#TODO: NullPointer class?

class FutureAddress(object):
    """Represents an address which is currently unknown."""
    
    def __init__(self, name="", real_addr=None):
        self.name = name
        self.real_addr = real_addr

    def resolve(self, env):
        if self.real_addr is None:
            real_addr = env[self.name]
            self.real_addr = real_addr
        return self.real_addr

    def __add__(self, other):
        if isinstance(other, FutureAddress):
            return FutureAddressOp(lambda x,y: x + y, self, other)
        elif isinstance(other, Address):
            ot = FutureAddress(real_addr=other)
            return self + ot
        else:
            assert False

class FutureAddressOp(object):
    """Represents a binary expression tree for FutureAddresses."""
    
    def __init__(self, op=None, fa1, fa2=None):
        self.op = op
        self.fa1 = fa1
        self.fa2 = fa2

    def resolve(self, env):
        if self.fa2 is None:
            if op is None:
                return self.fa1.resolve(env)
            else:
                return op(self.fa1.resolve(env))
        else:
            return op(self.fa1.resolve(env), self.fa2.resolve(env))

    def __add__(self, other):
        if isinstance(other, FutureAddressOp) or isinstance(other, FutureAddress):
            return FutureAddressOp(lambda x, y: x+y, self, other)
        elif isinstance(other, Address):
            ot = FutureAddress(real_addr=other)
            return self + ot
        else:
            assert False

#TODO: also verify bank of where we're being written?
class FutureAddressWrite(object):
    """Represents a place to fill an unknown pointer."""

    def __init__(self, ptr, place, size, bank=None):
        self.ptr = ptr
        self.place = place
        self.bank = bank
        self.size = size
        
    def fill(rom, env):
        place = self.place.resolve(env)
        addr  = self.ptr.resolve(env)
        assert self.bank is None or addr.bank() == self.bank,
                "Pointer's bank ({}) does not match expected bank ({})".format(addr.bank(), self.bank)
        rom.write_to_new(place, addr.as_snes_bytes())

