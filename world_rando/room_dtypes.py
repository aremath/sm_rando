from .coord import *
from .concrete_map import *
from .map_viz import *
from .room_viz import *
from data_types import basicgraph

class Room(object):

    def __init__(self, cmap, size, room_id, pos, graph=None):
        self.enemies = []
        self.plms = []
        self.doors = []
        if graph is None:
            self.graph = basicgraph.BasicGraph()
        else:
            self.graph = graph
        self.cmap = cmap
        self.size = size
        self.room_id = room_id
        self.pos = pos

        self.up_scroll = 0x70
        self.down_Scroll = 0xa0

    def translate(self):
        #produce a Jake room from this
        pass

    def viz_cmap(self, directory):
        fname = directory + "/room" + str(self.room_id) + "_cmap.png"
        map_viz(self.cmap, fname, "encoding/map_tiles")

    def viz_graph(self, directory):
        fname = directory + "/room" + str(self.room_id) + "_graph"
        self.graph.visualize(fname)

    #TODO...
    def viz_level(self, directory):
        fname = directory + "/room" + str(self.room_id) + "_level.png"
        room_viz(self.level_data, fname, "encoding/room_tiles")

#TODO: Door needs to contain some info about what ROOMS it connects, not just what tiles...
# or maybe the tiles on the cmap know what room they are in.
class Door(object):

    def __init__(self, tile, direction, room1, room2, door_id):
        self.pos = tile
        self.direction = direction
        self.origin = room1
        self.destination = room2
        self.id = door_id

    #def __hash__(self):
    #    #TODO: is this a valid equivalence relation?
    #    return hash(self.tiles)

# TODO: grand unified theory with ConcreteMap
# Holds the level data for a room
class Level(object):
    
    def __init__(self, dimensions, tiles=None):
        self.dimensions = dimensions
        if tiles is None:
            self.tiles = {}
        else:
            self.tiles = tiles

    def in_bounds(self, coord):
        return coord.in_bounds(Coord(0,0), self.dimensions)

    def assert_in_bounds(self, coord):
        assert self.in_bounds(coord), "Out of bounds: " + str(coord)

    def compose(self, other, collision_policy="error"):
        new_tiles = {}
        for c, t in self.items():
            new_tiles[c] = t
        for c, t in other.items():
            self.assert_in_bounds(c)
            if c in new_tiles:
                if collision_policy == "defer":
                    continue
                elif collision_policy == "error":
                    assert False, "Collision in compose: " + str(c)
                elif collision_policy == "overwrite":
                    new_tiles[c] = t
                else:
                    assert False, "Bad collision policy: " + collision_policy
            else:
                new_tiles[c] = t
        return Level(self.dimensions, tiles=new_tiles)

    def missing_defaults(self, mk_default):
        """Add the missing tiles using mk_default as a tile constructor"""
        for c in self.itercoords():
            if c not in self:
                self[c] = mk_default()

    def to_bytes(self):
        """Build the uncompressed level data. Errors if there is a tile missing"""
        level1 = b""
        bts = b""
        level2 = b""
        for c in self.itercoords():
           t = self[c]
           level1 += t.level1_bytes()
           bts += t.bts_bytes()
           #TODO l2
        size_bytes = int.to_bytes(len(level1), 2, byteorder="little")
        assert len(size_bytes) == 2, "Level too large!"
        return size_bytes + level1 + bts + level2
                
    def itercoords(self):
        """Iterator over the Coord that are within self,
        in x-minor order (or as the tiles would be laid out in the level data)"""
        for y in range(0, self.dimensions.y):
            for x in range(0, self.dimensions.x):
                yield Coord(x, y)

    # Behaves like a dictionary
    def __getitem__(self, key):
        return self.tiles[key]
    def __setitem__(self, key, value):
        if self.in_bounds(key):
            self.tiles[key] = value
        else:
            assert False, "Index not in bounds: " + str(key)
    def __len__(self):
        return len(self.tiles)
    def __contains__(self, item):
        return item in self.tiles
    def keys(self):
        return self.tiles.keys()
    def items(self):
        return self.tiles.items()
    def values(self):
        return self.tiles.values()

# The level data for a room is made up of Tiles
class Tile(object):

    def __init__(self, texture, tile_type):
        """ texture is an index into the texture table
            tflips is a (bool, bool) indicating horizontal and vertical flip
            for the texture.
            tile_type is a definition for the physical behavior of the tile, which
            includes """
        self.texture = texture
        self.tile_type = tile_type

    #TODO: safety assertions like hflip, vflip are one bit
    def level1_bytes(self):
        """The 2-byte part of the tile that is stored in the level1 foreground data."""
        n_texture = self.texture.index
        n_hflip = self.texture.flips[0] << 10
        n_vflip = self.texture.flips[1] << 11
        n_ttype = self.tile_type.index << 12
        n_all = n_texture | n_hflip | n_vflip | n_ttype
        return n_all.to_bytes(2, byteorder="little")

    def bts_bytes(self):
        """The 1-byte bts number."""
        return self.tile_type.bts.to_bytes(1, byteorder='little')

    #TODO...
    def level2_bytes(self):
        """The 2-byte part of the tile stored in the level2 background data."""
        return b''

# These are separate because for the purposes of waveform collapse, the type of a tile
# can be known while the texture remains unknown and vice versa.

# The visual properties of a tile
# Flips are hflip, vflip
class Texture(object):

    def __init__(self, index, flips):
        self.index = index
        self.flips = flips

# The physical properties of a tile
class Type(object):
    
    def __init__(self, index, bts):
        self.index = index
        self.bts = bts

