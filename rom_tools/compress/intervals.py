
def assert_bits(i, n):
    """Asserts that i has only n bits"""
    assert (n >= 0) and (n < (1 << n)), "n too large!"

# How many bits is the integer representation of i?
def count_bits(n):
    assert n >= 0
    i = 0
    while (n >> i) != 0:
        i = i + 1
    return i

def cmd_to_bytes(code, n):
    assert_bits(n, 5)
    cmdcode_int = code | n
    cmdcode_byte = cmdcode_int.to_bytes(1, byteorder='big')
    return cmdcode_byte

def extended_cmd_to_bytes(code, n):
    assert_bits(n, 10)
    cmdcode = (7 << 5) | (code >> 3)
    cmdcode_int = (cmdcode << 8) | n
    cmdcode_byte = cmdcode_int.to_bytes(2, byteorder='big')
    return cmdcode_byte

# bytes as binary string for printing
def bin_bytes(b):
    b_str = ""
    for i in range(len(b)):
        b_str += "{0:08b}".format(b[i]) #bin(b[i])
        b_str += " "
    return b_str
    

normal_max = 31
extended_max = 1023

#TODO: abstract?
#TODO: byte order??
class Interval(object):
    code = None

    def __init__(self, start, end, code, command_arg):
        self.start = start
        self.end = end
        self.code = code
        # The number of bytes the interval represents from the uncompressed data
        self.n = end - start
        assert self.n > 0
        # Compute the bytes for self
        if count_bits(self.n) <= 5:
            self.b = cmd_to_bytes(self.code, self.n) + command_arg
        elif count_bits(self.n) <= 10:
            self.b = extended_cmd_to_bytes(self.code, self.n) + command_arg
        else:
            #TODO: multiple extended commands when the region is very large!
            assert False, "TODO"
        # The number of bytes the compressed representation takes up
        self.rep = len(self.b)

    def to_str(self):
        return str(self.start) + "->" + str(self.end)

# Directly copy the next n bytes
class DirectCopyInterval(Interval):
    code = 0
    
    def __init__(self, start, end, cpy_bytes):
        super().__init__(start, end, DirectCopyInterval.code, cpy_bytes)
        self.cpy_bytes = cpy_bytes
        assert len(cpy_bytes) == self.n

    def __repr__(self):
       return "DirectCopy" + super().to_str() 

# Copy the following byte n times
class ByteFillInterval(Interval):
    code = 1 << 5
    
    def __init__(self, start, end, byte):
        super().__init__(start, end, ByteFillInterval.code, byte)
        self.byte = byte
        assert len(byte) == 1

    def __repr__(self):
       return "ByteFill" + super().to_str() 

# Copy the following 2-byte word n times
class WordFillInterval(Interval):
    code = 2 << 5

    def __init__(self, start, end, word):
        super().__init__(start, end, WordFillInterval.code, word)
        self.word = word
        assert len(word) == 2

    def __repr__(self):
       return "WordFill" + super().to_str()

# Fill n bytes with b, b+1, b+2, ...
class SigmaFillInterval(Interval):
    code = 3 << 5

    def __init__(self, start, end, byte):
        super().__init__(start, end, SigmaFillInterval.code, byte)
        self.byte = byte
        assert len(byte) == 1

    def __repr__(self):
       return "SigmaFill" + super().to_str() 

# Copy n bytes starting at the 2-byte address provided
class AddressCopyInterval(Interval):
    code = 4 << 5

    def __init__(self, start, end, addr):
        addr_bytes = self.addr.to_bytes(2, byteorder='big')
        super().__init__(start, end, AddressCopyInterval.code, addr_bytes)
        self.addr = addr

    def __repr__(self):
       return "AddressCopy" + super().to_str()

# Copy n bytes as above, but XOR each with 0xFF first
class AddressCopyXORInterval(Interval):
    code = 5 << 5

    def __init__(self, start, end, addr):
        addr_bytes = self.addr.to_bytes(2, byteorder='big')
        super().__init__(start, end, AddressCopyXORInterval, addr_bytes)
        self.addr = addr

    def __repr__(self):
       return "AddressCopyXOR" + super().to_str()

# Copy n bytes from the current offset minus the provided address
class RelativeAddressCopyInterval(Interval):
    code = 6 << 5

    def __init__(self, start, end, rel_addr):
        rel_addr_bytes = self.rel_addr.to_bytes(1, byteorder='big')
        super().__init__(start, end, RelativeAddressCopyInterval.code, rel_addr_bytes)
        self.rel_addr = rel_addr

    def __repr__(self):
       return "RelAddressCopy" + super().to_str()

# true if i1 is a subinterval of i2
#   starts later than i2 and ends earlier than i2.
def is_subinterval(i1, i2):
    return (i1.start >= i2.start) and (i1.end <= i2.end)

# i1 is worse than i2 if it takes up a smaller region and is represented with
# strictly more bytes
def is_worse(i1, i2):
    return is_subinterval(i1, i2) and i1.rep > i2.rep

# Look through src to find bytefill intervals
def find_bytefills(src):
    intervals = []
    i = 0
    while i < len(src):
        i2 = i
        while (i2 < len(src)) and (src[i] == src[i2]):
            i2 += 1
        interval_len = i2 - i
        # Only worth it if the same byte is repeated more than once
        # since the code takes up two bytes, but a direct copy will
        # take up three.
        if interval_len > 1:
            interval = ByteFillInterval(i, i2, src[i:i+1])
            intervals.append(interval)
        # We only need to consider the longest bytefill - shorter ones
        # will be generated later during the shortening step.
        i = i2
    return intervals

