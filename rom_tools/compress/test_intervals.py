from intervals import *

src1 = b"\x01\x01\x01\x01"
bf1 = find_bytefills(src1)
print(bf1)
assert len(bf1) == 1

src2 = b"\x01" * 34
bf2 = find_bytefills(src2)
print(bf2)
print(bf2[0].b)
print(bin_bytes(bf2[0].b))
