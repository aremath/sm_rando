import itertools
from collections import Counter
from collections import defaultdict
# Wavefunction collapse for room generation
# inspiration from : https://github.com/mxgmn/WaveFunctionCollapse
# Each "pixel" is in a superposition of possible pixel values
# In this case, the possible values are indexes into the physical tile table
# as well as the tile palette table.
#
# We first break the input up into n x n tiles, then match the tiles with the
# input, which might be completely blank.
# For each pixel, we store what tiles match in the area surrounding it, and
# the values that the pixel would have if each of those tiles was actually at
# that location.
# The result is a weighted probability distribution over the possible
# pixel values for that location. We then choose to fill the
# *most constrained* pixel by choosing a value from its probability
# distribution. Repeating this process eventually produces a value
# for every pixel (or perhaps leaving a few pixels with no matching tiles)

# Takes the output image (which can be blank)
# and creates a counter for each pixel of what pixel values it could be
def init_matches(im, tiles):
    # key - position
    # key - pixel value
    # value - number of times that pixel value could be used here
    matches = defaultdict(Counter)
    #TODO

#TODO
def recalc_matches(matches, pos):
    pass

# Will putting tile at im[loc] work?
def matches(tile, pos, im):
    for t in tile:
        p = eltwise_plus(pos, t)
        # Doesn't match if im has no data or if the tiles don't match
        if p not in im or not eltwise_match(tile[t], im[p]):
            return False
    return True

# Note:
# "image" in this case refers to an n-dimensional array of k-tuples
# implemented as a dictionary where
# key = n-tuple position
# value = k-tuple pixel
# can work over an "incomplete" image, but won't generate tiles
# for places where an incomplete index would be inside a tile
# TODO: generate "unconstrained" pixels where the image is incomplete!
def get_tiles(im, tile_size):
    # key - position
    # value - tile from im at that position
    tiles = {}
    # For every point of the image
    for i in im:
        # key - position offset
        # value - "pixel" value
        tile = {}
        # Generate a tile
        for t in multirange(tile_size):
            pos = eltwise_plus(t1, t2)
            if pos not in im:
                tile = None
            else:
                tile[t] = im[pos]
        tiles[i] = tile
    return tiles

# Get iterator over all possible values of indexes into a table of the given size
def multirange(sizes):
    return itertools.product(*[range(i) for i in sizes])

def eltwise_plus(t1, t2):
    return tuple(map(sum, zip(t1, t2)))

def eltwise_match(t1, t2):
    eq = [i1 == i2 for (i1, i2) in zip(t1, t2)]
    return all(eq)

