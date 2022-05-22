from enum import IntEnum
import numpy as np
from collections import namedtuple

# Copy from ../world_rando/coord.py
Coord = namedtuple("Coord", ("x", "y"))

class TileType(IntEnum):
    Air = 0             # BTS 0
    Slope = 1           # BTS is slope index + flips
    Air_Fool_Xray = 2   # BTS 2 -> spike block with no collision
    Treadmill = 3       # BTS 8 / 9 -> R / L conveyor, BTS 82 -> Quicksand, BTS 85 -> Sandfall
    AirShot = 4         # Unused
    HCopy = 5
    Air2 = 6            # Unused
    AirBomb = 7         # Unused
    Solid = 8
    Door = 9
    Spike = 10
    Crumble = 11
    Shot = 12
    VCopy = 13
    Grapple = 14
    Bomb = 15

class Texture(object):
    def __init__(self, texture_index, hflip, vflip):
        self.texture_index = texture_index
        self.hflip = hflip
        self.vflip = vflip

    def __repr__(self):
        return (self.texture_index, self.hflip, self.vflip).__repr__()

class Tile(object):
    def __init__(self, tile_type, texture):
        self.tile_type = tile_type
        self.texture = texture

    def to_bytes(self):
        t = self.tile_type << 12
        h = self.texture.hflip << 11
        v = self.texture.vflip << 10
        ti = self.texture.texture_index
        tile = t | h | v | ti
        return tile.to_bytes(2, byteorder="little")

class LevelArrays(object):
    def __init__(self, layer1, bts, layer2):
        self.layer1 = layer1
        self.bts = bts
        self.layer2 = layer2

def tile_of_bytes(b, layer1=True):
    assert len(b) == 2
    i = int.from_bytes(b, byteorder="little")
    ttype = i >> 12
    assert ttype in list(TileType), "Bad tiletype: {}, {}".format(ttype, bin(i))
    # Ensure level does not use unused tile types
    if layer1:
        assert ttype != 4 and ttype != 6 and ttype != 7, "Bad tiletype: {}, {}".format(ttype, bin(i))
    hflip = (i >> 11) & 1
    vflip = (i >> 10) & 1
    tindex = i & 0b1111111111
    texture = Texture(tindex, hflip, vflip)
    return Tile(ttype, texture)

# Translates the (uncompressed) leveldata bytes to arrays of Layer1, BTS, Layer2
# Layer2 is None if all zeros
# levelsize is the number of bytes in the decompressed level1 data
# = 2 * the number of BTS bytes
# = the number of level2 bytes
def level_array_from_bytes(levelbytes, dimensions):
    # First two bytes are the amount of level1 data
    levelsize = int.from_bytes(levelbytes[0:2], byteorder='little')
    # Cut off the size
    levelbytes = levelbytes[2:]
    # Make sure everything matches
    assert levelsize % 2 == 0, "Purported level size {} is not even!".format(levelsize)
    # Some vanilla levels have more level data than needed! :(
    assert levelsize >= dimensions.x * dimensions.y * 2, "Level data length {} does not match specified room dimensions {}".format(levelsize, dimensions.x * dimensions.y * 2)
    #assert levelsize == dimensions.x * dimensions.y * 2, "Level data length {} does not match specified room dimensions {}".format(levelsize, dimensions.x * dimensions.y * 2)
    # The level might not include level2 data
    if len(levelbytes) == int(2.5 * levelsize):
        has_layer2 = True
    elif len(levelbytes) == int(1.5 * levelsize):
        has_layer2 = False
    else:
        assert False, "Purported level size {} does not match actual level size {}".format(1.5 * levelsize, len(levelbytes))
    layer1 = np.empty(dimensions, dtype="object")
    bts = np.empty(dimensions, dtype="int")
    if has_layer2:
        layer2 = np.empty(dimensions, dtype="object")
    else:
        layer2 = None
    for y in range(dimensions.y):
        for x in range(dimensions.x):
            index = y * dimensions.x + x
            layer1_index = index * 2
            layer1[x][y] = tile_of_bytes(levelbytes[layer1_index:layer1_index+2])
            bts_index = index + levelsize
            bts_data = int.from_bytes(levelbytes[bts_index:bts_index+1], byteorder='little')
            bts[x][y] = bts_data
            if has_layer2:
                layer2_index = index + (3 * levelsize//2)
                layer2[x][y] = tile_of_bytes(levelbytes[layer2_index:layer2_index+2], layer1=False)
    return LevelArrays(layer1, bts, layer2)

def bytes_from_level_array(level_arrays):
    all_layer1_bytes = bytearray(b"")
    all_bts_bytes = bytearray(b"")
    all_layer2_bytes = bytearray(b"")
    xdim, ydim = level_arrays.layer1.shape
    for y in range(ydim):
        for x in range(xdim):
            l1 = level_arrays.layer1[x][y]
            bts = level_arrays.bts[x][y]
            for b in l1.to_bytes():
                all_layer1_bytes.append(b)
            for b in int(bts).to_bytes(1, byteorder="little"):
                all_bts_bytes.append(b)
            if level_arrays.layer2 is not None:
                l2 = level_arrays.layer2[x][y]
                for b in l2.to_bytes():
                    all_layer2_bytes.append(b)
    all_bytes = all_layer1_bytes + all_bts_bytes
    if level_arrays.layer2 is not None:
        all_bytes = all_bytes + all_layer2_bytes
    # Create the size header
    head = int.to_bytes(len(all_layer1_bytes), 2, byteorder="little")
    # Convert back to bytes
    all_bytes = head + bytes(all_bytes)
    return all_bytes

def bits(x, size):
    return [(x & 2**i) >> i for i in range(size)]

def reverse_bits(bits):
    x = 0
    for i,b in enumerate(bits):
        x = x | ((2**i) * b)
    return x

def bit_array_from_bytes(levelbytes, dimensions):
    # First two bytes are the amount of level1 data
    levelsize = int.from_bytes(levelbytes[0:2], byteorder='little')
    # Cut off the size
    levelbytes = levelbytes[2:]
    # Make sure everything matches
    assert levelsize % 2 == 0, "Purported level size {} is not even!".format(levelsize)
    assert levelsize == dimensions.x * dimensions.y * 2, "Level data length {} does not match specified room dimensions {}".format(levelsize, dimensions.x * dimensions.y * 2)
    # The level might not include level2 data
    if len(levelbytes) == int(2.5 * levelsize):
        has_level2 = True
    elif len(levelbytes) == int(1.5 * levelsize):
        has_level2 = False
    else:
        assert False, "Purported level size {} does not match actual level size {}".format(1.5 * levelsize, len(levelbytes))
    levelarray = np.zeros((dimensions.x, dimensions.y, 40), dtype=np.uint8)
    for y in range(dimensions.y):
        for x in range(dimensions.x):
            # Level 1 data
            index = y * dimensions.x + x
            level1index = index * 2
            level1 = int.from_bytes(levelbytes[level1index:level1index+2], byteorder='little')
            for i, b in enumerate(bits(level1, 16)):
                levelarray[(x, y, i)] = b
            # BTS data
            btsindex = index + levelsize
            bts = int.from_bytes(levelbytes[btsindex:btsindex+1], byteorder='little')
            bts_offset = 16
            for i, b in enumerate(bits(bts, 8)):
                levelarray[(x, y, i+bts_offset)] = b
            # Level 2 (background) data
            level2_offset = 24
            if has_level2:
                level2index = int(index * 2 + 3*(levelsize/2))
                level2 = int.from_bytes(levelbytes[level2index:level2index+2], byteorder='little')
                for i, b in enumerate(bits(level2, 16)):
                    levelarray[(x, y, i+level2_offset)] = b
    return levelarray

def codebook_from_bit_array(a):
    library = set([])
    for v in a.reshape((-1, a.shape[-1])):
        library.add(tuple(v))
    return np.array(list(library), dtype=int)

def quantize(a, codebook):
    out = np.zeros(a.shape, dtype=codebook.dtype)
    for (x, y), _ in np.ndenumerate(out[:,:,0]):
        ds = np.sum((a[x,y,:] - codebook) ** 2, axis=1)
        closest_index = np.argmin(ds)
        out[x,y,:] = codebook[closest_index]
    return out

def bytes_from_bit_array(level_array):
    xdim, ydim, bits = level_array.shape
    assert bits == 40
    # Store in (mutable) bytearray instead of immutable bytes
    # for much faster time
    all_layer1_bytes = bytearray(b"")
    all_bts_bytes = bytearray(b"")
    all_layer2_bytes = bytearray(b"")
    for y in range(ydim):
        for x in range(xdim):
            # Level 1
            l1_bits = level_array[x,y,0:16]
            l1_int = int(reverse_bits(l1_bits))
            l1_bytes = l1_int.to_bytes(2, byteorder='little')
            # Have to use a for-loop because we get 2 bytes
            for b in l1_bytes:
                all_layer1_bytes.append(b)
            # BTS
            bts_bits = level_array[x,y,16:24]
            bts_int = int(reverse_bits(bts_bits))
            bts_bytes = bts_int.to_bytes(1, byteorder='little')
            for b in bts_bytes:
                all_bts_bytes.append(b)
            # Level 2
            l2_bits = level_array[x,y,24:40]
            l2_int = int(reverse_bits(l2_bits))
            l2_bytes = l2_int.to_bytes(2, byteorder='little')
            for b in l2_bytes:
                all_layer2_bytes.append(b)
    # Ignore layer2 data if all zeros
    has_layer2 = False
    for b in all_layer2_bytes:
        if b != 0:
            has_layer2 = True
    all_bytes = all_layer1_bytes + all_bts_bytes
    if has_layer2:
        all_bytes = all_bytes + all_layer2_bytes
    # Create the size header
    head = int.to_bytes(len(all_layer1_bytes), 2, byteorder="little")
    # Convert back to bytes
    all_bytes = head + bytes(all_bytes)
    return all_bytes

