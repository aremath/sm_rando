from world_rando.coord import *
from world_rando.concrete_map import *
from world_rando.map_viz import *
from world_rando.room_viz import *
from data_types import basicgraph

class Room(object):

    def __init__(self, cmap, size, room_id, pos, region, graph=None):
        self.enemies = []
        self.plms = []
        self.doors = []
        self.items = []
        if graph is None:
            self.graph = basicgraph.BasicGraph()
        else:
            self.graph = graph
        self.cmap = cmap
        self.size = size
        self.room_id = room_id
        self.pos = pos
        #TODO: more aesthetic info
        self.region = region

        #TODO: why are we doing this here?
        self.up_scroll = 0x70
        self.down_Scroll = 0xa0
        # Filled later
        self.level = None

    #TODO
    def translate(self):
        #Produce a ROM room from this
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
        room_viz(self.level, fname, "encoding/room_tiles")

class Door(object):
    """
    Holds the info for a door
    """

    def __init__(self, tile, direction, room1, room2, name):
        self.pos = tile
        self.direction = direction
        self.origin = room1
        self.destination = room2
        self.name = name

    #def __hash__(self):
    #    #TODO: is this a valid equivalence relation?
    #    return hash(self.tiles)

class Item(object):
    """
    Holds the data for an item
    """

    def __init__(self, item_type, map_pos):
        # String - the actual item contained here
        # Second index to the dict in rom_tools/item_definitions.py
        self.item_type = item_type
        # Coord - position of the item in the concrete map for the room
        self.map_pos = map_pos
        # String - one of "C", "N", "H" for Chozo, Hidden, Normal
        # First index to the item definition in rom_tools/item_definitions.py
        self.graphic = None
        # Coord - position of the item in the room
        self.room_pos = None

#TODO: grand unified theory with ConcreteMap
#TODO: This data structure should be in rom_tools since
# other tools that interact with the rom might need access to
# this kind of level info.
class Level(object):
    """
    Holds the level data for a room
    """
    
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

    def matches(self, other, pos):
        """Can other be put into self at pos without conflict?"""
        for c in other.itercoords():
            nc = c + pos
            if self.in_bounds(nc) and nc in self:
                # other can be put onto self by being made /more specific/
                # if the specified are of self is a refinement of the entire
                # other pattern, then it is a match.
                if not self[nc].is_subtile(other[c]):
                    return False
            else:
                return False
        return True

    def reflect(self, axis):
        reflected = Level(self.dimensions)
        perp = Coord(1,1) - axis
        size = self.dimensions * axis
        for c, t in self.tiles.items():
            axis_c = c * axis
            new_axis_c = size - axis_c - axis
            reflected_c = new_axis_c + (c * perp)
            reflected[reflected_c] = t.reflect(axis)
        return reflected

    def find_matches(self, other):
        matches = []
        for c in self.itercoords():
            if self.matches(other, c):
                matches.append(c)
        return matches

    def find_matches_in_rect(self, other, rect):
        matches = []
        for c in rect.as_list():
            if self.matches(other, c):
                matches.append(c)
        return matches

    def compose(self, other, collision_policy="error", offset=Coord(0,0)):
        """
        Composes with another Level
        """
        new_tiles = {}
        for c, t in self.items():
            new_tiles[c] = t
        for c, t in other.items():
            c_mod = c + offset
            self.assert_in_bounds(c_mod)
            if c_mod in new_tiles:
                if collision_policy == "defer":
                    continue
                elif collision_policy == "error":
                    assert False, "Collision in compose: " + str(c_mod)
                elif collision_policy == "overwrite":
                    new_tiles[c_mod] = t
                # Favor self in conflicts where self is a subtile of other.
                # Otherwise error
                elif collision_policy == "refine":
                    if self[c_mod].is_subtile(t):
                        continue
                    else:
                        assert False, "Collision in compose: " + str(c_mod)
                else:
                    assert False, "Bad collision policy: " + collision_policy
            else:
                new_tiles[c_mod] = t
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
        """
        Iterator over the Coord that are within self,
        in x-minor order (or as the tiles would be laid out in the level data)
        """
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

    def __eq__(self, other):
        return self.texture == other.texture and self.tile_type == other.tile_type

    # Is self a subtile of other
    def is_subtile(self, other):
        return self.texture.is_sub(other.texture) and self.tile_type.is_sub(other.tile_type)
    
    def reflect(self, axis):
        if self.texture.is_any:
            r_tex = self.texture
        else:
            r_tex = self.texture.reflect(axis)
        if self.tile_type.is_any:
            r_ty = self.tile_type
        else:
            r_ty = self.tile_type.reflect(axis)
        return Tile(r_tex, r_ty)

    #TODO: safety assertions like hflip, vflip are one bit
    def level1_bytes(self):
        """The 2-byte part of the tile that is stored in the level1 foreground data."""
        n_texture = self.texture.index
        n_hflip = self.texture.flips[0] << 11
        n_vflip = self.texture.flips[1] << 10
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

def reflect_flips(flips, axis):
    """
    Change the flips to reflect about axis
    Vertical flip changes if axis is (0,1)
    Horizontal flip changes if axis is (1,0)
    """
    return ((flips[0] + axis.x) % 2, (flips[1] + axis.y) % 2)

# These are separate because for the purposes of waveform collapse, the type of a tile
# can be known while the texture remains unknown and vice versa.

#TODO: the is_any thing is kind of awkward...
class Texture(object):
    """
    The visual properties of a tile
    Flips are hflip, vflip
    """

    def __init__(self, index, flips, is_any=False):
        self.is_any = is_any
        if is_any:
            self.index = None
            self.flips = None
        else:
            self.index = index
            self.flips = flips

    def __eq__(self, other):
        return self.index == other.index and self.flips == other.flips

    def is_sub(self, other):
        """
        Is self a subtile of other?
        """
        return self == other or other.is_any

    def reflect(self, axis):
        return Texture(self.index, reflect_flips(self.flips, axis))

class Type(object):
    """
    The physical properties of a tile
    """
    
    def __init__(self, index, bts, is_any=False):
        self.is_any = is_any
        if is_any:
            self.index = None
            self.bts = None
        else:
            self.index = index
            self.bts = bts

    def __eq__(self, other):
        return self.index == other.index and self.bts == other.bts

    def is_sub(self, other):
        """
        Is self a subtile of other?
        """
        return self == other or other.is_any

    def get_slope_info(self):
        assert self.index == 0x01, "Tile is not a slope!"
        # Top bit is unused
        # Next two bits are flips
        hflip = (self.bts >> 6) & 0b1
        vflip = (self.bts >> 7) & 0b1
        # Then a 5-bit index into the slope table
        index = self.bts & 0b11111
        return hflip, vflip, index
    
    def reflect(self, axis):
        # Must change the flips it if it is a slope
        if self.index == 0x01:
            hflip, vflip, index = self.get_slope_info()
            # Reflect the flips
            hflip, vflip = reflect_flips((hflip, vflip), axis)
            new_bts = index | (vflip << 7) | (hflip << 6)
            return Type(self.index, new_bts)
        # If it isn't a slope, then it will be symmetrical and flipping does not change it
        #TODO: that isn't strictly true (ex. conveyors)
        else:
            return Type(self.index, self.bts)


