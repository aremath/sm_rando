import byte_ops


class Address(object):
    """Address Class that handles conversions
       this way we don't have to rememver which 'kind' of address we have
       just which kind we want to use"""
    def __init__(self):
        return

    def from_SNES(self,addr):
        byte_ops.assert_valid_SNES(addr)
        self.pc_addr = byte_ops.SNES_to_PC(addr)

    def from_PC(self,addr):
        self.pc_addr = addr

    def as_PC(self):
        return self.pc_addr

    def as_SNES(self):
        sn = byte_ops.PC_to_SNES(self.pc_addr)
        byte_ops.assert_valid_SNES(sn)
        return sn

    def as_SNES_endian(self):
        sn = self.as_SNES()
        return byte_ops.int_split(sn)

    def as_room_id(self):
        return byte_ops.addr_to_room_id(self.as_SNES())

    def as_room_id_endian(self):
        return byte_ops.int_split(self.as_room_id())

    def copy_increment(self,inc):
        ad = self.as_PC() + inc
        new = Address()
        new.from_PC(ad)
        return new
