import random

def random_bytes(n):
    out = b""
    for _ in range(n):
        b_int = random.randint(0,255)
        out += b_int.to_bytes(1, byteorder='big')
    return out

# Restrict to a certain number of bytes
def random_r_bytes(n, p):
    out = b""
    assert p >= 0
    assert p < 256
    for _ in range(n):
        b_int = random.randint(0,p)
        out += b_int.to_bytes(1, byteorder='big')
    return out

# Given two bytestrings, what indices are they different?
def differs(b1, b2):
    assert len(b1) == len(b2), "Different lengths: " + str(len(b1)) + ", " + str(len(b2))
    differs = []
    for i in range(len(b1)):
        if b1[i] != b2[i]:
            differs.append((i, b1[i], b2[i]))
    return differs
