from intervals import *
from compress import *
from decompress import *
from util import *

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

#src = b"\x02\x03\x02\x03\x02\x03"
#wf = find_wordfills(src)
#assert len(wf) == 1
#src = b"\x01\x02\x02\x02\x02\x03" * 2
#assert len(compress(src)) == 9
#src = b"\x02\x02\x02\x05\x01\x02\x03\x04"
#assert len(compress(src)) == 7
## test overlaps
#src = b"\x01\x01\x01\x01\x02\x03\x04\x05"
#out = compress(src)
##f = open("dst.bin", "wb")
##f.write(out)
##f.close()
#src = b"\x01\x02\x01\x04"*2
#assert len(compress(src)) == 8

def assert_same(s1, s2):
    d = differs(s1, s2)
    assert len(d) == 0, str(d)

def test(n_bytes, resolution):
    src = random_r_bytes(n_bytes, resolution)
    c = compress(src)
    dc = decompress(c)
    assert_same(src, dc)

#for i in range(100):
#    test(256, 16)

src = random_r_bytes(256, 8)
bytes_to_file("testing/raw.b", src)
c = compress(src)
bytes_to_file("testing/press.b", c)
c = bytes_from_file("testing/press.b")
dc = decompress(c)
assert_same(src, dc)

#src = b"\x01\x02\x03\x02\x03\x02\x03"
#wf = find_wordfills(src)
#print(wf)

