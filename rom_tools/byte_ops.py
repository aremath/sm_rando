
def valid_SNES(addr):
    """Checks a givven snes lorom address to see if it is a valid adress"""
    if (addr < 0) or (addr >0x1000000):
        return False
    else:
        m = ((addr & 0xFF0000) >> 16) % 2 == 0
        b = addr & 0x8000 != 0
        return m != b

def assert_valid_SNES(addr):
    if not valid_SNES(addr):
        raise IndexError
    else:
        return addr

def PC_to_SNES(addr):
    """ Converts from a PC rom adress to a snes lorom one"""
    a = ((addr << 1) & 0xFF0000) + 0x800000
    b = addr & 0xFFFF
    return a|b


def SNES_to_PC(addr):
    """Converts LORAM addresses to PC Addresses."""
    return ((addr & 0x7f0000) >> 1) | (addr & 0x7FFF)

def int_split(n):
    """ Splits and Endians pointers for "ROM MODE" """
    l = []
    a=n
    while a > 0:
        l = l + [a&0xFF]
        a = a >> 8
    return l

def room_id_to_SNES(id):
    """takes a room id (address bank $8F) and create the actual snes address
       assumes leading 7 isn't there"""
    return 0x8f0000 | id

def addr_to_room_id(self, addr):
	return addr & 0xFFFF
