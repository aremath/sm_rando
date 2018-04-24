
def validSNES(addr):
    """Checks a givven snes lorom address to see if it is a valid adress"""
    if (addr < 0) or (addr >0x1000000):
        return False
    else:
        m = ((addr & 0xFF0000) >> 16) % 2 == 0
        b = addr & 0x8000 != 0
        return m != b

def assertValid(addr):
    if not _validSNES(addr):
        raise IndexError
    else:
        return addr

def PCtoSNES(addr):
    """ Converts from a PC rom adress to a snes lorom one"""
    a = ((addr << 1) & 0xFF0000) + 0x800000
    b = addr & 0xFFFF
    return a|b


def SNEStoPC(addr):
    """Converts LORAM addresses to PC Addresses."""
    return ((addr & 0x7f0000) >> 1) | (addr & 0x7FFF)

def intSplit(n):
    """ Splits and Endians pointers for "ROM MODE" """
    l = []
    a=n
    while a > 0:
        l = l + [a&0xFF]
        a = a >> 8
    return l
