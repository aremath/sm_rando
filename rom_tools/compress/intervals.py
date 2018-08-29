
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

def shorten_check(start, end, new_end):
    assert new_end < end and new_end > start

normal_max = 31
extended_max = 1023

#TODO: abstract?
#TODO: byte order??
class Interval(object):
    code = None

    def __init__(self, start, end, code, command_arg, factor=1):
        self.start = start
        self.end = end
        self.code = code
        # The number of bytes the interval represents from the uncompressed data
        self.n = end - start
        assert self.n > 0
        # n must be divisble by factor since an interval that takes up n bytes with a factor
        # of two will have an input variable of n/2.
        assert self.n % factor == 0
        # Command(x) copies x + 1 bytes. So to copy n bytes, use command(n-1)
        # Factor takes care of the wordfill special case, where one of n
        # corresponds to two bytes filled
        n_adj = (self.n // factor) - 1
        # Compute the bytes for self
        if count_bits(n_adj) <= 5:
            self.b = cmd_to_bytes(self.code, n_adj) + command_arg
        elif count_bits(n_adj) <= 10:
            self.b = extended_cmd_to_bytes(self.code, n_adj) + command_arg
        else:
            #TODO: multiple extended commands when the region is very large!
            assert False, "TODO"
        # The number of bytes the compressed representation takes up
        self.rep = len(self.b)

    def to_str(self):
        return str(self.start) + "->" + str(self.end)

    def shorten(self, new_end):
        assert new_end < end and new_end > start
        return None

    # Hashing for graph-as-dictionary implementation.
    def __hash__(self):
        return hash(self.b)

    # Comparison for heapq
    def __lt__(self, other):
        return self.b < other.b

# Directly copy the next n bytes
class DirectCopyInterval(Interval):
    code = 0
    
    def __init__(self, start, end, cpy_bytes):
        super().__init__(start, end, DirectCopyInterval.code, cpy_bytes)
        self.cpy_bytes = cpy_bytes
        assert len(cpy_bytes) == self.n, str(len(cpy_bytes)) + ", " + str(self.n)

    def __repr__(self):
       return "DirectCopy" + super().to_str()

    def shorten(self, new_end):
        shorten_check(self.start, self.end, new_end)
        return DirectCopyInterval(self.start, new_end, cpy_bytes[:(new_end - self.start)])

# Copy the following byte n times
class ByteFillInterval(Interval):
    code = 1 << 5
    
    def __init__(self, start, end, byte):
        super().__init__(start, end, ByteFillInterval.code, byte)
        self.byte = byte
        assert len(byte) == 1

    def __repr__(self):
       return "ByteFill" + super().to_str()

    def shorten(self, new_end):
        shorten_check(self.start, self.end, new_end)
        return ByteFillInterval(self.start, new_end, self.byte)

# Copy the following 2-byte word n times
#TODO: a wordfill can capture 64 bytes of input when n is 32: discrepancy between n and
# start-end
# TODO: n is 0<n<33 not -1<n<31...
class WordFillInterval(Interval):
    code = 2 << 5

    def __init__(self, start, end, word):
        super().__init__(start, end, WordFillInterval.code, word, factor=2)
        self.word = word
        assert len(word) == 2

    def __repr__(self):
       return "WordFill" + super().to_str()

    def shorten(self, new_end):
        # n must be a multiple of two
        adj_end = self.end // 2
        shorten_check(self.start, self.end, adj_end)
        return WordFillInterval(self.start, adj_end, self.word)

# Fill n bytes with b, b+1, b+2, ...
class SigmaFillInterval(Interval):
    code = 3 << 5

    def __init__(self, start, end, byte):
        super().__init__(start, end, SigmaFillInterval.code, byte)
        self.byte = byte
        assert len(byte) == 1

    def __repr__(self):
       return "SigmaFill" + super().to_str()

    def shorten(self, new_end):
        shorten_check(self.start, self.end, new_end)
        return SigmaFillInterval(self.start, new_end, self.byte)

# Copy n bytes starting at the 2-byte address provided
class AddressCopyInterval(Interval):
    code = 4 << 5

    def __init__(self, start, end, addr):
        addr_bytes = self.addr.to_bytes(2, byteorder='big')
        super().__init__(start, end, AddressCopyInterval.code, addr_bytes)
        self.addr = addr

    def __repr__(self):
       return "AddressCopy" + super().to_str()

    def shorten(self, new_end):
        shorten_check(self.start, self.end, new_end)
        return AddressCopyInterval(self.start, new_end, self.addr)

# Copy n bytes as above, but XOR each with 0xFF first
class AddressCopyXORInterval(Interval):
    code = 5 << 5

    def __init__(self, start, end, addr):
        addr_bytes = self.addr.to_bytes(2, byteorder='big')
        super().__init__(start, end, AddressCopyXORInterval, addr_bytes)
        self.addr = addr

    def __repr__(self):
       return "AddressCopyXOR" + super().to_str()

    def shorten(self, new_end):
        shorten_check(self.start, self.end, new_end)
        return AddressCopyXORInterval(self.start, new_end, self.addr)

# Copy n bytes from the current offset minus the provided address
class RelativeAddressCopyInterval(Interval):
    code = 6 << 5

    def __init__(self, start, end, rel_addr):
        rel_addr_bytes = self.rel_addr.to_bytes(1, byteorder='big')
        super().__init__(start, end, RelativeAddressCopyInterval.code, rel_addr_bytes)
        self.rel_addr = rel_addr

    def __repr__(self):
       return "RelAddressCopy" + super().to_str()

    def shorten(self, new_end):
        shorten_check(self.start, self.end, new_end)
        return RelativeAddressCopyInterval(self.start, new_end, self.rel_addr)

# A placeholder interval used to make start and end nodes in the graph
class FakeInterval(Interval):
    
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.rep = 0
        self.b = b""

    def __repr__(self):
        return "FAKE" + super().to_str()

    def shorten(self, new_end):
        assert False, "No Shorten for fake intervals!"

# true if i1 is a subinterval of i2
#   starts later than i2 and ends earlier than i2.
def is_subinterval(i1, i2):
    return (i1.start >= i2.start) and (i1.end <= i2.end)

# i1 is worse than i2 if it takes up a smaller region and is represented with
# strictly more bytes.
# Note: use strictly because we don't want to eliminate i1 < i2 then eliminate i2 < i1
# if they are the same. (Or eliminate i1 < i1)
def is_worse(i1, i2):
    return is_subinterval(i1, i2) and i1.rep > i2.rep

def filter_worse(intervals):
    new_intervals = []
    for i1 in intervals:
        irrelevant = False
        for i2 in intervals:
            if is_worse(i1,i2):
                irrelevant = True
        if not irrelevant:
            new_intervals.append(i1)
    return new_intervals

# Look through src to find intervals
# pattern is src -> i1 -> i2 -> bool
# constructor is src -> i1 -> i2 -> Interval
# Constructs intervals using constructor based on runs of true pattern evaluations
def find_pattern(src, pattern, constructor, factor=1):
    intervals = []
    i1 = 0
    while i1 < len(src):
        i2 = i1
        # Count the length of the bytes matching pattern after i
        while (i2 < len(src)) and pattern(src, i1, i2):
            i2 += factor
        interval_len = i2 - i1
        # Only worth it if the pattern is true more than once
        # since the code takes up two bytes, but a direct copy will
        # take up three.
        if interval_len > 1:
            interval = constructor(src, i1, i2)
            intervals.append(interval)
        # We only need to consider the longest pattern - shorter ones
        # will be generated later during the shortening step.
        # This if is here because src[i1] doesn't necessarily match pattern
        # If it doesn't we still need to make forward progress.
        if i1 == i2:
            i1 += 1
        else:
            i1 = i2
    return intervals

# Byte Fills
def bytefill_pattern(src, i1, i2):
    return src[i1] == src[i2]

def bytefill_constructor(src, i1, i2):
    return ByteFillInterval(i1,  i2, src[i1:i1+1])

def find_bytefills(src):
    return find_pattern(src, bytefill_pattern, bytefill_constructor)

# Word Fills
def wordfill_pattern(src, i1, i2):
    # If i2 is the index of the last byte, the second matching byte does not exist
    if i2 + 1 < len(src):
       return src[i1] == src[i2] and src[i1 + 1] == src[i2 + 1] 
    else:
        return False

def wordfill_constructor(src, i1, i2):
    return WordFillInterval(i1, i2, src[i1:i1+2])

def find_wordfills(src):
    return find_pattern(src, wordfill_pattern, wordfill_constructor, factor=2)

# Sigma Fills
def sigmafill_pattern(src, i1, i2):
    n = i2 - i1
    return src[i2] == (src[i1] + n) % 256

def sigmafill_constructor(src, i1, i2):
    return SigmaFillInterval(i1, i2, src[i1:i1+1])

def find_sigmafills(src):
    return find_pattern(src, sigmafill_pattern, sigmafill_constructor)

