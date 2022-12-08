from world_rando.coord import *
from world_rando.concrete_map import *
from world_rando.map_viz import *
from world_rando.room_viz import *
from data_types import basicgraph

from rom_tools import rom_data_structures as rd
from rom_tools import leveldata_utils
from rom_tools import item_definitions

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
        self.down_scroll = 0xa0
        # Filled later
        self.level = None
        self.converter = None

    #TODO
    def translate(self):
        #Produce a ROM room from this
        pass

    def viz_cmap(self, directory, map_tiles):
        fname = directory + "/room" + str(self.room_id) + "_cmap.png"
        map_viz(self.cmap, fname, map_tiles)

    def viz_graph(self, directory):
        fname = directory + "/room" + str(self.room_id) + "_graph"
        self.graph.visualize(fname)

    #TODO...
    def viz_level(self, directory, room_tiles):
        fname = directory + "/room" + str(self.room_id) + "_level.png"
        room_viz(self.level, fname, room_tiles)

    def __repr__(self):
        return f"Room: {self.room_id}\n{self.graph}"

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
        # Filled later
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
                # Other can be put onto self by being made /more specific/
                # If the specified area of self is a refinement of the entire
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
                # If the tile can be refined, refine it. Otherwise, overwrite
                #TODO: TileFunctions?
                elif collision_policy == "try_refine":
                    if self[c_mod].is_subtile(t):
                        continue
                    else:
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
            #TODO Layer 2
        size_bytes = int.to_bytes(len(level1), 2, byteorder="little")
        assert len(size_bytes) == 2, "Level too large!"
        return size_bytes + level1 + bts + level2

    def __repr__(self):
        level_s = []
        for y in range(0, self.dimensions.y):
            line = []
            for x in range(0, self.dimensions.x):
                line += str(self[Coord(x, y)].tile_type)
            line = "|".join(line)
            level_s.append(line)
        return "\n".join(level_s)

                
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

    def __repr__(self):
        if self.index == 0:
            return " "
        elif self.index == 1 or self.index == 8:
            return "#"
        else:
            return "@"

#
# Conversion to ROM data types
#
#TODO: consider using ROM data types from the start?

# ObjNames that also keeps track of PLM ID.
#TODO: automatic tracking on object create?
# Can check if a PLM object
#TODO: automatic tracking of save station IDs
class ObjNamesConvert(rd.ObjNames):

    def __init__(self, plm_id=0):
        super().__init__()
        self.plm_id = plm_id

    # Automatic tracking and assignment of PLM IDs
    def create(self, constructor, *args, replace=None, obj_name=None):
        if constructor is rd.PLM:
            args = (*args, self.plm_id)
        obj = super().create(constructor, *args, replace=replace, obj_name=obj_name)
        if constructor is rd.PLM:
            self.plm_id += 1
        return obj

def convert_rooms(rooms, parsed_rooms=None):
    # Keeps track of global PLM ids for non-returning PLMs like items
    #TODO: Merge with existing (parsed) ObjNames ?
    # compile_from_savestations will handle the DFS to only compile reachable rooms!
    #TODO: find out how many PLM ids there are, and which ones are used in the base game
    #TODO: Some PLMs (i.e. opposing door caps) should be assigned the same ID
    obj_names = ObjNamesConvert(plm_id=0)
    # rooms is room_id -> Room
    # Rooms handshake on what to call their headers so that
    # pointers can be created before the room they point to
    #TODO: Save Stations
    # Remember to use names when passing pointer-like values to obj_names.create 
    # (rather than the object itself)
    default_converter = Converter()
    for room in rooms:
        #print(room.room_id)
        # Can do this even though rooms are interlinked because of the shared room header pointer naming format
        if room.converter is None:
            _ = default_converter.convert_roomheader(room, obj_names)
        else:
            assert parsed_rooms is not None, "Trying to copy details without parsed rooms!"
            c = room.converter(parsed_rooms)
            _ = c.convert_roomheader(room, obj_names)
    return obj_names

# room_id
room_header_name_f = "room_header_id_{}"
# region_name, id
room_id_f = "{}{}"

def get_room_pointer(room):
    area_index = room.region.region_id
    rid = room_id_f.format(area_index, room.room_id)
    return room_header_name_f.format(rid)

# 0   Right
# 1   Left
# 2   Down
# 3   Up
# 4+  Door spawns a closing door cap
# For now, always spawning a closing door cap
def get_door_orientation(direction):
    if direction == Coord(1,0):
        return 4
    elif direction == Coord(-1,0):
        return 5
    elif direction == Coord(0, 1):
        return 6
    elif direction == Coord(0, -1):
        return 7

class Converter(object):
    """
    Class with static methods that convert generated data structures to the rom_tools format
    Allows replacing any / all of the methods with different ones.
    """
    #TODO: how to enforce this kind of thing in the tiles, when the door index must be known by door tiles
    # but might change during conversion?

    def __init__(self):
        pass

    # RoomHeader
    def convert_roomheader(self, room, obj_names):
        statechooser = self.convert_statechooser(room, obj_names)
        doorlist = self.convert_door_list(room.doors, obj_names)
        #TODO
        room_index = 0
        area_index = room.region.region_id
        map_x, map_y = room.pos
        width, height = room.size
        CRE_bitset = set() # Refer to rom_tools/rom_data_structures.
        # Room Header
        roomheader = obj_names.create(rd.RoomHeader, room_index, area_index, map_x, map_y, width, height,
                room.up_scroll, room.down_scroll, CRE_bitset, doorlist.name, statechooser.name,
                obj_name=get_room_pointer(room))
        return roomheader

    #TODO: this can become more complex
    # StateChooser
    #   StateChoice
    def convert_statechooser(self, room, obj_names):
        room_state = self.convert_roomstate(room, obj_names)
        # All rooms are default for now
        statechooser = obj_names.create(rd.StateChooser, [], room_state.name)
        return statechooser

    # RoomState
    def convert_roomstate(self, room, obj_names):
        print(f"Room: {room.room_id}")
        fx = self.convert_fx(room, obj_names)
        enemylist = self.convert_enemies([], obj_names)
        enemytypes = self.convert_enemytypes([], obj_names)
        plmlist = self.convert_plms(room.items, obj_names)
        level = self.convert_level(room.level, obj_names)
        scrolls = self.convert_scrolls(room, obj_names)
        # Room State
        #TODO: set these extra params
        tileset = 0
        music_data = 0
        music_track = 0
        layer2_scroll_x = 0
        layer2_scroll_y = 0
        special_xray = None
        main_asm = None
        background_index = None
        setup_asm = None
        room_state = obj_names.create(rd.RoomState, level.name,
                tileset, music_data, music_track, fx.name, enemylist.name, enemytypes.name,
                layer2_scroll_x, layer2_scroll_y, scrolls.name, special_xray, main_asm,
                plmlist.name, background_index, setup_asm)
        return room_state

    #TODO: FX
    # FX
    #   FXEntry
    #   FX
    def convert_fx(self, room, obj_names):
        fx = obj_names.create(rd.FX, [], None)
        return fx

    #TODO
    # EnemyList
    #   Enemies
    def convert_enemies(self, enemies, obj_names):
        enemylist = obj_names.create(rd.EnemyList, [], 0)
        return enemylist

    # EnemyTypes
    def convert_enemytypes(self, enemies, obj_names):
        # Enemy Types
        #   EnemyType
        enemytypes = obj_names.create(rd.EnemyTypes, [])
        return enemytypes

    #TODO: other PLMs like door caps, gates, etc.
    # PLMList
    def convert_plms(self, items, obj_names):
        #   PLMs
        plms = []
        # Item PLMs
        for item in items:
            i = self.convert_item(item, obj_names)
            plms.append(i)
        plmlist = obj_names.create(rd.PLMList, [p.name for p in plms])
        return plmlist

    # PLM - Items
    def convert_item(self, item, obj_names):
        #TODO: just have item_definitions be a big dict
        ids = item_definitions.make_item_definitions()
        print(f"Item: {item.item_type}, {item.graphic}")
        #print(item.item_type)
        item_id = int.from_bytes(ids[item.item_type][item.graphic], byteorder="little")
        ix, iy = item.room_pos
        # PID assigned automatically by special create
        i = obj_names.create(rd.PLM, item_id, ix, iy)
        return i

    # Level Data
    def convert_level(self, level, obj_names):
        #print(level)
        lbytes = level.to_bytes()
        larray = leveldata_utils.level_array_from_bytes(lbytes, level.dimensions)
        level = obj_names.create(rd.LevelData, lbytes, larray, None)
        return level

    # Scrolls
    def convert_scrolls(self, room, obj_names):
        # All green
        #TODO: more nuanced scrolls
        rx, ry = room.level.dimensions
        scroll_array = np.zeros((rx // 16, ry // 16))
        for x in range(rx // 16):
            for y in range(ry // 16):
                scroll_array[x,y] = 2
        scrolls = obj_names.create(rd.Scrolls, scroll_array)
        return scrolls

    # DoorList
    def convert_door_list(self, doors, obj_names):
        new_doors = []
        for door in doors:
            #TODO: door.destination is just the ID without the region??
            # IDs should be unique across multiple regions anyways...
            #TODO: door.tiles doesnt make sense when the door transitions between regions though.
            # Get the pointer to what will be the target room
            dest_id = door.destination
            #TODO: Door needs to have this info ahead of time
            dest_region = 0
            dest_rid = room_id_f.format(dest_region, dest_id)
            room_ptr = room_header_name_f.format(dest_rid)
            d = self.convert_door(door, room_ptr, obj_names)
            new_doors.append(d)
        doorlist = obj_names.create(rd.DoorList, [door.name for door in new_doors])
        return doorlist

    # Door
    #TODO: elevator properties
    def convert_door(self, door, room_ptr, obj_names):
        elevator_properties = 0
        orientation = get_door_orientation(door.direction)
        #TODO: appropriate defaults for orientation
        xlow = 0
        ylow = 0
        xhigh = 0
        yhigh = 0
        dist = 0
        door_asm = None
        door_obj = obj_names.create(rd.Door, room_ptr, elevator_properties, orientation,
                xlow, ylow, xhigh, yhigh, dist, door_asm)
        return door_obj

class DetailCopyConverter(Converter):

    def __init__(self, replace_with, replace_from):
        """
        to_replace is an object name (RoomHeader)
        replace_from is an ObjNames containing to_replace
        """
        self.replace_header = replace_from[replace_with]
        assert type(self.replace_header) is rd.RoomHeader

    def convert_roomheader(self, room, obj_names):
        room_name = get_room_pointer(room)
        doorlist = self.convert_door_list(room.doors, obj_names)
        map_x, map_y = room.pos
        #fields = ["room_index", "area_index", "map_x", "map_y", "width", "height", "scroll_up",
        #        "scroll_down", "CRE_bitset", "door_list", "state_chooser"]
        replace = [None, room.region.region_id, map_x, map_y, None, None, None,
                None, None, doorlist, None]
        # Bring in the room+dependencies from the other namespace
        rh = obj_names.copy_obj(self.replace_header, replace=replace, new_name=room_name)
        return rh

    # Save door properties from each door as well
    #TODO: allocate the new door_list on top of the old one using old_address and old_size?
    def convert_door_list(self, doors, obj_names):
        new_doors = []
        # This requires doors are listed in the same order as the original room!
        for door, old_door in zip(doors, self.replace_header.door_list.l):
            #TODO: door.destination is just the ID without the region??
            # IDs should be unique across multiple regions anyways...
            #TODO: door "tiles" don't make sense when the door transitions between regions though.
            # Get the pointer to what will be the target room
            dest_id = door.destination
            #print(dest_id)
            #print(d)
            dest_region = 0
            dest_rid = room_id_f.format(dest_region, dest_id)
            room_ptr = room_header_name_f.format(dest_rid)
            d = self.convert_door(door, room_ptr, old_door, obj_names)
            new_doors.append(d)
        doorlist = obj_names.create(rd.DoorList, [door.name for door in new_doors])
        return doorlist

    # Door
    # Use the old door info
    #TODO: want to use the old door info for doors that go INTO this room...
    def convert_door(self, door, room_ptr, old_door, obj_names):
        elevator_properties = old_door.elevator_properties
        orientation = old_door.orientation
        xlow = old_door.x_pos_low
        ylow = old_door.y_pos_low
        xhigh = old_door.x_pos_high
        yhigh = old_door.y_pos_high
        dist = old_door.spawn_distance
        door_asm = old_door.asm_pointer
        door_obj = obj_names.create(rd.Door, room_ptr, elevator_properties, orientation,
                xlow, ylow, xhigh, yhigh, dist, door_asm)
        return door_obj

#TODO: SaveStation room mker + converter that actually edits the state
