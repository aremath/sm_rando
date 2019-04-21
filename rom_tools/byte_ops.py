
def valid_snes(addr):
    """Checks a given snes lorom address to see if it is a valid adress"""
    if addr < 0 or addr > 0xffffff or addr & 0xfe0000 == 0x7e0000 or addr & 0x408000 == 0x000000:
        return False
    else:
        return True

def valid_pc(addr):
    if addr < 0 or addr >= 0x400000:
        return False
    else:
        return True

def assert_valid_snes(addr):
    if not valid_snes(addr):
        raise IndexError
    else:
        return addr

def assert_valid_pc(addr):
    if not valid_pc(addr):
        raise IndexError
    else:
        return addr

def pc_to_snes(addr):
    """ Converts a PC address to a lorom address."""
    assert_valid_pc(addr)
    a = ((addr << 1) & 0x7f0000) + 0x800000
    b = (addr & 0x7fff) + 0x8000
    snes = a|b
    assert_valid_snes(snes)
    return snes

def snes_to_pc(addr):
    assert_valid_snes(addr)
    """Converts a lorom address to a PC address."""
    assert_valid_snes(addr)
    pc = ((addr & 0x7f0000) >> 1) | (addr & 0x7fff)
    assert_valid_pc(pc)
    return pc

def assert_n_bits(i, n):
    assert (i >= 0) and (i < (1 << n)), "i too large!"

# TODO: Are these needed?
def room_id_to_snes(id):
    """takes a room id (address bank $8F) and create the actual snes address
       assumes leading 7 isn't there"""
    return 0x8f0000 | id

def addr_to_room_id(self, addr):
	return addr & 0xFFFF

