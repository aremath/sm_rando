from .room_dtypes import *
from .coord import *
import os

#TODO: more advanced DSL that can handle things like input for door id and size...

def parse_pattern(pattern_filename):
    f = open(pattern_filename, "r")
    tiles = {}
    max_tile = Coord(0,0)
    max_area = 0
    for y, line in enumerate(f.readlines()):
        for x, entry in enumerate(line.split()):
            assert entry[0] == "["
            assert entry[-1] == "]"
            entry = entry[1:-1]
            es = entry.split(",")
            # Assume BTS
            if len(es) == 2:
                bts = 0
            elif len(es) == 3:
                bts = int(es[2], 16)
            else:
                assert False, "Bad entry: " + entry
            # Find the texture
            if es[0] == "_":
                texture = "ANY"
            else:
                tex_index, flips = find_flips(es[0])
                texture = Texture(tex_index, flips)
            # Find the type
            if es[1] == "_":
                tile_type = "ANY"
            else:
                ty_index = int(es[1], 16)
                ty = Type(ty_index, bts)
            c = Coord(x, y)
            a = c.area()
            tiles[c] = Tile(texture, ty)
            if a > max_area:
                max_tile = c
                max_area = a
    f.close()
    level = Level(max_tile + Coord(1,1), tiles=tiles)
    return level

def find_flips(entry):
    flips = (0,0)
    es = entry.split("|")
    main_entry = int(es[0], 16)
    if len(es) == 3:
        hflip = int(es[1])
        vflip = int(es[2])
        flips = (hflip, vflip)
    elif len(es) != 1:
        assert False, "Bad Entry!"
    return main_entry, flips

def load_patterns(path):
    # Get all the filenames in path
    fnames = [f for f in os.listdir(path) if os.path.isfile(os.path.join(f, path))]
    patterns = {}
    for f in fnames:
        name, ext = f.split(".")
        if ext == "txt":
            p = parse_pattern(os.path.join(f, path))
            patterns[name] = p
    return patterns
