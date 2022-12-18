
# i is the int from which to get bits (one byte)
# n is the number of bits to get
# p is where to start getting them from (indexed from 0 is the high bit of i)
from typing import Callable, Sequence


def get_n_bits(i, n, p):
    end = (8 - n - p)
    assert end >= 0
    mask = (2**n - 1) << end
    return (i & mask) >> end


def decompress_with_size(src: Sequence[int], debug: bool = False) -> tuple[bytes, int]:
    dst = b""
    index = 0
    while True:
        if debug:
            print("Current Index: {}".format(index))
        next_cmd = src[index]
        if next_cmd == 0xff:
            index += 1
            break
        # The command code is the top 3 bits
        cmd_code = get_n_bits(next_cmd, 3, 0)
        if cmd_code == 7:
            # An extended command uses the next 3 bits for the actual command
            cmd_code = get_n_bits(next_cmd, 3, 3)
            # Get the integer which is the last 10 bits of the 2-byte command
            n_bytes = [next_cmd & 0b11, src[index+1]]
            n = int.from_bytes(n_bytes, byteorder='big')
            # Set the index higher - the argument bytes will be collected from after
            # the 2-byte code
            index += 2
        else:
            n = get_n_bits(next_cmd, 5, 3)
            index += 1
        # Arg is adjusted by 1 since ex. direct_copy 0 copies 1 byte
        adj_n = n + 1
        # Find the alg to use
        cmd: Callable[[int, int, Sequence[int], bytes, bool], tuple[bytes, int]]
        if cmd_code == 0:
            cmd = direct_copy
        elif cmd_code == 1:
            cmd = bytefill
        elif cmd_code == 2:
            cmd = wordfill
        elif cmd_code == 3:
            cmd = sigmafill
        elif cmd_code == 4:
            cmd = addr_copy
        elif cmd_code == 5:
            cmd = addr_xor_copy
        elif cmd_code == 6:
            cmd = rel_addr_copy
        else:
            assert False, "Bad cmd_code: " + str(cmd_code)
        # Use the cmd to compute the new bytes of dst
        # and the new index into src (the index of the next command)
        new, index = cmd(adj_n, index, src, dst, debug)
        # Add the decoded bytes to the dst
        dst += new
    return dst, index

def decompress(src: Sequence[int], debug: bool = False) -> bytes:
    dst, index = decompress_with_size(src, debug=debug)
    return dst

def direct_copy(n, index, src, dst, debug):
    arg = src[index:index+n]
    if debug:
        print("DIRECTCOPY({}) from {} to {} of size {}".format(arg, len(dst), len(dst) + n, hex(n)))
    assert len(arg) == n, (len(arg), n)
    return arg, index + n

def bytefill(n, index, src, dst, debug):
    arg = src[index:index+1]
    if debug:
        print("BYTEFILL from {} to {} of size {}".format(len(dst), len(dst) + n, hex(n)))
    out = n * arg
    assert len(out) == n
    return out, index+1

def n_bytes_of_word(n, word):
    whole = n // 2
    half = n % 2
    out = whole * word + half * word[0:1]
    return out

def wordfill(n, index, src, dst, debug):
    arg = src[index:index+2]
    if debug:
        print("WORDFILL from {} to {} of size {}".format(len(dst), len(dst) + n, hex(n)))
    out = n_bytes_of_word(n, arg)
    assert len(out) == n
    return out, index+2

def sigmafill(n, index, src, dst, debug):
    arg = src[index]
    out = b""
    for i in range(n):
        argi = (arg + i) % 256
        out += argi.to_bytes(1, byteorder='little')
    if debug:
        print("SIGMAFILL from {} to {} of size {}".format(len(dst), len(dst) + n, hex(n)))
    assert len(out) == n
    return out, index+1

def addr_copy(n, index, src, dst, debug):
    arg_bytes = src[index:index+2]
    arg = int.from_bytes(arg_bytes, byteorder='little')
    to_copy = get_copy_bytes(arg, arg + n, dst)
    if debug:
        print("ADDRCPY({}) from {} to {} of size {}".format(arg, len(dst), len(dst) + n, hex(n)))
        print(to_copy)
    assert len(to_copy) == n #TODO
    return to_copy, index+2

def map_bytes(op, byte):
    out = b""
    for b in byte:
        out += op(b).to_bytes(1, byteorder='little')
    return out

def addr_xor_copy(n, index, src, dst, debug):
    arg_bytes = src[index:index+2]
    arg = int.from_bytes(arg_bytes, byteorder='little')
    to_copy = get_copy_bytes(arg, arg+n, dst, lambda x: x^0xff)
    if debug:
        print("ADDRXORCPY({}) from {} to {} of size {}".format(arg, len(dst), len(dst) + n, hex(n)))
        print(to_copy)
    assert len(to_copy) == n, (len(to_copy), n)
    return to_copy, index+2

def get_copy_bytes(index0, index1, dst, op=lambda x: x):
    """Get the bytes between index0 and index1 in dst. If index1 is past the end of dst, then this wraps as many
    times as is necessary to simulate those bytes being already copied."""
    # TODO: Allow my own compression to use this feature...
    buf = b""
    # While still within the existing buffer, copy from it
    while index0 < index1 and index0 < len(dst):
        buf += map_bytes(op, dst[index0:index0+1])
        index0 += 1
    # When you overrun, begin copying from yourself
    i = 0
    while index0 < index1:
        buf += map_bytes(op, buf[i:i+1])
        i += 1
        index0 += 1
    return buf

def rel_addr_copy(n, index, src, dst, debug):
    # One byte
    arg = src[index]
    # Can't use negative indexing because n-arg can be zero
    index0 = len(dst) - arg
    index1 = len(dst) + n - arg
    to_copy = get_copy_bytes(index0, index1, dst)
    if debug:
        print("ADDRRELCPY({}) from {} to {} of size {}".format(arg, len(dst), len(dst) + n, hex(n)))
        print(to_copy)
    assert len(to_copy) == n, (len(to_copy), n, index0, index1)
    return to_copy, index+1

#TODO rel_addr_xor_copy: an extended command with cmd-code 7 is a relative address xor copy!
