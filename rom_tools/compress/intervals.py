
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
    assert new_end < end and new_end > start, str(start) + ", " + str(end) + ": " + str(new_end)

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
        # Command(x) copies x + 1 bytes. So to copy n bytes, use command(n-1)
        n_adj = self.n - 1
        # Compute the bytes for self
        if count_bits(n_adj) <= 5:
            self.b = cmd_to_bytes(self.code, n_adj) + command_arg
        elif count_bits(n_adj) <= 10:
            self.b = extended_cmd_to_bytes(self.code, n_adj) + command_arg
        else:
            #TODO: multiple extended commands when the region is very large!
            # - difficult because on copy commands, it will change the argument
            assert False, "TODO - Byte region too large!"
        # The number of bytes the compressed representation takes up
        self.rep = len(self.b)

    def to_str(self):
        return ":" + str(self.start) + "->" + str(self.end)

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
class WordFillInterval(Interval):
    code = 2 << 5

    def __init__(self, start, end, word):
        super().__init__(start, end, WordFillInterval.code, word)
        self.word = word
        assert len(word) == 2

    def __repr__(self):
       return "WordFill" + super().to_str()

    def shorten(self, new_end):
        shorten_check(self.start, self.end, new_end)
        return WordFillInterval(self.start, new_end, self.word)

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
        addr_bytes = addr.to_bytes(2, byteorder='little')
        super().__init__(start, end, AddressCopyInterval.code, addr_bytes)
        self.addr = addr

    def __repr__(self):
       return "AddressCopy" + super().to_str() #+ ":" + str(self.addr)

    def shorten(self, new_end):
        shorten_check(self.start, self.end, new_end)
        return AddressCopyInterval(self.start, new_end, self.addr)

# Copy n bytes as above, but XOR each with 0xFF first
class AddressCopyXORInterval(Interval):
    code = 5 << 5

    def __init__(self, start, end, addr):
        self.addr = addr
        addr_bytes = self.addr.to_bytes(2, byteorder='little')
        super().__init__(start, end, AddressCopyXORInterval.code, addr_bytes)

    def __repr__(self):
       return "AddressCopyXOR" + super().to_str()

    def shorten(self, new_end):
        shorten_check(self.start, self.end, new_end)
        return AddressCopyXORInterval(self.start, new_end, self.addr)

# Copy n bytes from the current offset minus the provided address
class RelativeAddressCopyInterval(Interval):
    code = 6 << 5

    def __init__(self, start, end, rel_addr):
        rel_addr_bytes = rel_addr.to_bytes(1, byteorder='big')
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

def choose_best_interval(intervals):
    base = intervals[0]
    saved = base.n - base.rep
    for i in intervals:
        i_saved = i.n - i.rep
        if i_saved < saved:
            base = i
            saved = i_saved
    return i

def find_pattern_at(src, i1, pattern, constructor, min_size):
    i2 = i1
    # Count the length of the bytes matching pattern after i
    while (i2 < len(src)) and pattern(src, i1, i2):
        i2 += 1
    interval_len = i2 - i1
    # Worth it if the pattern is true more than once
    # since the code takes up two bytes, but a direct copy will
    # take up at least three.
    if (interval_len > 1) and (interval_len >= min_size):
        interval = [constructor(src, i1, i2)]
    else:
        interval = []
    return interval, i2

# Look through src to find intervals
# pattern is src -> i1 -> i2 -> bool
# constructor is src -> i1 -> i2 -> Interval
# Size is the minimum size of intervals to find
# Constructs intervals using constructor based on runs of true pattern evaluations
def find_pattern(src, pattern, constructor, min_size, overlap=False):
    intervals = []
    i1 = 0
    while i1 < len(src):
        interval, i2 = find_pattern_at(src, i1, pattern, constructor, min_size)
        intervals.extend(interval)
        # We only need to consider the longest pattern - shorter ones
        # will be generated later during the shortening step.
        if overlap:
            # Overlap the ends by one byte in order to find overlapping word fills
            if i2 - i1 == 1:
                i1 += 1 # If we didn't find a word fill, advance normally
            else:
                i1 = i2 - 1 # If there was a possible word fill, advance to one /behind/ the end
        # No overlap: when the pattern ends, the next one begins without a possibility of
        # beginning within the original pattern
        else:
            i1 = i2
    return intervals

# Byte Fills
def bytefill_pattern(src, i1, i2):
    return src[i1] == src[i2]

def bytefill_constructor(src, i1, i2):
    return ByteFillInterval(i1,  i2, src[i1:i1+1])

def find_bytefill_at(src, i1, min_size):
    return find_pattern_at(src, i1, bytefill_pattern, bytefill_constructor, min_size)

def find_bytefills(src, min_size):
    return find_pattern(src, bytefill_pattern, bytefill_constructor, min_size)

# Word Fills
def wordfill_pattern(src, i1, i2):
    if i1 %2 == i2 % 2:
        return src[i1] == src[i2]
    else:
        return src[i1+1] == src[i2]

def wordfill_constructor(src, i1, i2):
    return WordFillInterval(i1, i2, src[i1:i1+2])

def find_wordfill_at(src, i1, min_size):
    return find_pattern_at(src, i1, wordfill_pattern, wordfill_constructor, min_size)

def find_wordfills(src, min_size):
    return find_pattern(src, wordfill_pattern, wordfill_constructor, min_size, overlap=True)

# Sigma Fills
def sigmafill_pattern(src, i1, i2):
    n = i2 - i1
    return src[i2] == (src[i1] + n) % 256

def sigmafill_constructor(src, i1, i2):
    return SigmaFillInterval(i1, i2, src[i1:i1+1])

def find_sigmafill_at(src, i1, min_size):
    return find_pattern_at(src, i1, sigmafill_pattern, sigmafill_constructor, min_size)

def find_sigmafills(src, min_size):
    return find_pattern(src, sigmafill_pattern, sigmafill_constructor, min_size)

# How many bytes from i2 match i1?
def match_length(src, i1, i2, operation):
    n = 0
    # While the bytes match and the indices are in bounds...
    while i1 + n < len(src) and operation(src[i2 + n]) == src[i1 + n] and i2 + n < i1:
        n += 1
    # Subtract 1 because the above adds 1 during the last iteration when the condition is false.
    return n - 1

# All match lengths over the given range
def match_lens(src, i1, lower, upper, operation):
    return map(lambda i2: match_length(src, i1, i2, operation), range(lower, upper))

def find_copy_at(src, i1, cpy_range, constructor, min_size, operation=lambda x: x):
    lower, upper = cpy_range(i1)
    # Nothing to map
    if lower == upper:
        return []
    # Compute the length of copy for each possible copy location
    m_lens = list(match_lens(src, i1, lower, upper, operation))
    # The number of bytes to copy
    best_n = max(m_lens)
    # Where to copy them from
    best_l = m_lens.index(best_n) + lower
    # Copying a single byte costs at least two bytes...
    if (best_n > 1) and (best_n >= min_size):
        # Add one because the "end" of an interval is one past the actual last byte
        interval = [constructor(src, best_l, i1, i1 + best_n + 1)]
    else:
        interval = []
    return interval

def find_copy(src, cpy_range, constructor, min_size, operation=lambda x: x):
    intervals = []
    i1 = 0
    for i1 in range(len(src)):
        interval = find_copy_at(src, i1, cpy_range, constructor, min_size, operation)
        intervals.extend(interval)
    return intervals

# Address Copy
def address_range(i1):
    return (0, min(i1, (1 << 16) - 1))

def address_constructor(src, loc, i1, i2):
    return AddressCopyInterval(i1, i2, loc)

def find_address_copy_at(src, i1, min_size):
    return find_copy_at(src, i1, address_range, address_constructor, min_size)

def find_address_copies(src, min_size):
    return find_copy(src, address_range, address_constructor, min_size)

# Address XOR Copy
def address_xor_range(i1):
    return address_range(i1)

def address_xor_constructor(src, loc, i1, i2):
    return AddressCopyXORInterval(i1, i2, loc)

def find_address_xor_copy_at(src, i1, min_size):
    return find_copy_at(src, i1, address_xor_range, address_xor_constructor, min_size,
        operation=lambda x: x ^ 0xff)

def find_address_xor_copies(src, min_size):
    return find_copy(src, address_xor_range, address_xor_constructor, min_size,
        operation=lambda x: x ^ 0xff)

# Relative Copy
def rel_address_range(i1):
    return (max(0, i1 - 255), i1)

def rel_address_constructor(src, loc, i1, i2):
    return RelativeAddressCopyInterval(i1, i2, i1 - loc)

def find_rel_address_copy_at(src, i1, min_size):
    return find_copy_at(src, i1, rel_address_range, rel_address_constructor, min_size)

def find_rel_address_copies(src, min_size):
    return find_copy(src, rel_address_range, rel_address_constructor, min_size)

