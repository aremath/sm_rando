from intervals import *
from compress import *

src = b"\x01\x01\x01\x01"
bf = find_bytefills(src)
assert len(bf) == 1

src = b"\x01" * 34
bf = find_bytefills(src)
assert bf[0].rep == 3

src = b"\x01" * 32
bf = find_bytefills(src)
assert bf[0].rep == 2

src = b"\x01\x02\x03\x04\x01\x02\x03\x04"
sf = find_sigmafills(src)
assert len(sf) == 2

src = b"\x02\x03\x02\x03\x02\x03"
wf = find_wordfills(src)
assert len(wf) == 1
"""
src = b"\x01\x02\x02\x02\x02\x03" * 2
assert len(compress(src)) == 11
src = b"\x02\x02\x02\x05\x01\x02\x03\x04"
assert len(compress(src)) == 6
"""
# test overlaps
src = b"\x01\x01\x01\x01\x02\x03\x04\x05"
print(compress(src))
