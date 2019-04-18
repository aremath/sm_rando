
#TODO: This is not quite right...
def valid_snes(addr):
    """Checks a given snes lorom address to see if it is a valid adress"""
    if (addr < 0) or (addr >= 0x1000000):
        return False
    else:
        m = ((addr & 0xFF0000) >> 16) % 2 == 0
        b = addr & 0x8000 != 0
        return m != b

def assert_valid_snes(addr):
    if not valid_snes(addr):
        raise IndexError
    else:
        return addr

def pc_to_snes(addr):
    """ Converts from a PC rom adress to a snes lorom one"""
    a = ((addr << 1) & 0xff0000) + 0x800000
    b = (addr & 0x7fff) + 0x8000
    return a|b

def snes_to_pc(addr):
    """Converts LORAM addresses to PC Addresses."""
    assert (addr & 0xffff) >= 0x8000
    return ((addr & 0x7f0000) >> 1) | (addr & 0x7fff)

def assert_n_bits(i, n):
    assert (i >= 0) and (i < (1 << n)), "i too large!"

# TODO: Are these needed?
def room_id_to_snes(id):
    """takes a room id (address bank $8F) and create the actual snes address
       assumes leading 7 isn't there"""
    return 0x8f0000 | id

def addr_to_room_id(self, addr):
	return addr & 0xFFFF

