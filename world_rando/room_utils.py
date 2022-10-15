import numpy as np

from world_rando.room_dtypes import *
from world_rando.coord import *
from rom_tools import rom_data_structures as rd
from rom_tools import leveldata_utils
from rom_tools import item_definitions

### DEFAULT TILE TYPES ###

def mk_default_solid():
    tex = Texture(0x5f, (0,0))
    ty = Type(0x8, 0x0)
    return Tile(tex, ty)

def mk_default_air():
    tex = Texture(0xff, (0,0))
    ty = Type(0x0, 0x0)
    return Tile(tex, ty)
    
def mk_external():
    tex = Texture(0x6a, (0,0))
    ty = Type(0x8, 0x0)
    return Tile(tex, ty)

def mk_wall(level, map_xy, direction, thickness=2):
    """
    Make a wall from the default solid tile at the edge of the given maptile
    Can use similar code to make a wall of "solids" for wavecollapse
    """
    map_x = map_xy.x * 16
    map_y = map_xy.y * 16
    tstart = 16 - thickness
    if direction == up:
        r = Rect(Coord(map_x, map_y), Coord(map_x + 16, map_y + thickness))
    elif direction == down:
        r = Rect(Coord(map_x, map_y + tstart), Coord(map_x + 16, map_y + 16))
    elif direction == left:
        r = Rect(Coord(map_x, map_y), Coord(map_x + thickness, map_y + 16))
    elif direction == right:
        r = Rect(Coord(map_x + tstart, map_y), Coord(map_x + 16, map_y + 16))
    else:
        assert False, "Bad direction: " + str(direction)
    mk_default_rect(level, r)

def mk_rect(level, rect, tile_maker):
    """Paint a rectangle of the given tile on the level"""
    for c in rect.as_list():
        level[c] = tile_maker()

def mk_default_rect(level, rect):
    """Paint a rectangle of solid tiles on the level"""
    mk_rect(level, rect, mk_default_solid)

def mk_air_rect(level, rect):
    mk_rect(level, rect, mk_default_air)

#TODO: the four cardinal coords better represent the four directions
#p = Coord(1,1) - d.abs()
#c = p.scale(6)
#if direction > Coord(0,0):
#   c += direction.scale(16-size)
#return c
def find_door_pos(map_xy, direction, size=2):
    map_xy_s = map_xy.scale(16)
    if direction == up:
        add = Coord(6,0)
    elif direction == down:
        add = Coord(6, 16-size)
    elif direction == left:
        add = Coord(0, 6)
    elif direction == right:
        add = Coord(16-size, 6)
    else:
        assert False, "Bad direction: " + str(direction)
    return map_xy_s + add

# Makes a door (default-looking) at the edge of the given maptile
def mk_door(level, map_xy, direction, door_id, size=2):
    p = find_door_pos(map_xy, direction, size)
    if direction == up:
        door_fun = mk_up_door
    elif direction == down:
        door_fun = mk_down_door
    elif direction == left:
        door_fun = mk_left_door
    elif direction == right:
        door_fun = mk_right_door
    else:
        assert False, "Bad direction: " + str(direction)
    door_fun(level, p, door_id, size)

# Whee more spaghetti
# Door /leading/ up
# pos is the top-left corner of the door
def mk_up_door(level, pos, door_id, size):
    # Top row: doors
    level[pos + Coord(0,0)] = Tile(Texture(0x63, (1,1)), Type(0x09, door_id))
    level[pos + Coord(1,0)] = Tile(Texture(0x62, (1,1)), Type(0x09, door_id))
    level[pos + Coord(2,0)] = Tile(Texture(0x62, (0,1)), Type(0x09, door_id))
    level[pos + Coord(3,0)] = Tile(Texture(0x63, (0,1)), Type(0x09, door_id))

    if size < 2:
        assert False

    if size > 2:
        # Second row (optional + empty)
        level[pos + Coord(0,1)] = Tile(Texture(0x63, (1,1)), Type(0x00, 0x00))
        level[pos + Coord(1,1)] = Tile(Texture(0x62, (1,1)), Type(0x00, 0x00))
        level[pos + Coord(2,1)] = Tile(Texture(0x62, (0,1)), Type(0x00, 0x00))
        level[pos + Coord(3,1)] = Tile(Texture(0x63, (0,1)), Type(0x00, 0x00))

    if size == 4:
        # Third row (optional + empty)
        level[pos + Coord(0,2)] = Tile(Texture(0x43, (1,1)), Type(0x00, 0x00))
        level[pos + Coord(1,2)] = Tile(Texture(0x42, (1,1)), Type(0x00, 0x00))
        level[pos + Coord(2,2)] = Tile(Texture(0x42, (0,1)), Type(0x00, 0x00))
        level[pos + Coord(3,2)] = Tile(Texture(0x43, (0,1)), Type(0x00, 0x00))

    if size > 5:
        assert False

    # Last row, shot block, h-copies
    level[pos + Coord(0,size-1)] = Tile(Texture(0x37, (1,1)), Type(0x0C, 0x43))
    level[pos + Coord(1,size-1)] = Tile(Texture(0x36, (1,1)), Type(0x05, 0xFF))
    level[pos + Coord(2,size-1)] = Tile(Texture(0x36, (0,1)), Type(0x05, 0xFE))
    level[pos + Coord(3,size-1)] = Tile(Texture(0x37, (0,1)), Type(0x05, 0xFD))

def mk_down_door(level, pos, door_id, size):
    # Top row: shot blocks and h-copies
    level[pos + Coord(0,0)] = Tile(Texture(0x37, (1,0)), Type(0x0C, 0x42))
    level[pos + Coord(1,0)] = Tile(Texture(0x36, (1,0)), Type(0x05, 0xFF))
    level[pos + Coord(2,0)] = Tile(Texture(0x36, (0,0)), Type(0x05, 0xFE))
    level[pos + Coord(3,0)] = Tile(Texture(0x37, (0,0)), Type(0x05, 0xFD))

    if size < 2:
        assert False

    if size > 2:
        # Second row (optional + empty)
        level[pos + Coord(0,1)] = Tile(Texture(0x43, (1,0)), Type(0x00, 0x00))
        level[pos + Coord(1,1)] = Tile(Texture(0x42, (1,0)), Type(0x00, 0x00))
        level[pos + Coord(2,1)] = Tile(Texture(0x42, (0,0)), Type(0x00, 0x00))
        level[pos + Coord(3,1)] = Tile(Texture(0x43, (0,0)), Type(0x00, 0x00))

    if size == 4:
        # Third row (optional + empty)
        level[pos + Coord(0,2)] = Tile(Texture(0x63, (1,0)), Type(0x00, 0x00))
        level[pos + Coord(1,2)] = Tile(Texture(0x62, (1,0)), Type(0x00, 0x00))
        level[pos + Coord(2,2)] = Tile(Texture(0x62, (0,0)), Type(0x00, 0x00))
        level[pos + Coord(3,2)] = Tile(Texture(0x63, (0,0)), Type(0x00, 0x00))

    if size > 5:
        assert False

    # Last row, doors
    level[pos + Coord(0,size-1)] = Tile(Texture(0x63, (1,0)), Type(0x09, door_id))
    level[pos + Coord(1,size-1)] = Tile(Texture(0x62, (1,0)), Type(0x09, door_id))
    level[pos + Coord(2,size-1)] = Tile(Texture(0x62, (0,0)), Type(0x09, door_id))
    level[pos + Coord(3,size-1)] = Tile(Texture(0x63, (0,0)), Type(0x09, door_id))

def mk_right_door(level, pos, door_id, size):
    # Left row: shot blocks and h-copies
    level[pos + Coord(0,0)] = Tile(Texture(0x0C, (0,0)), Type(0x0C, 0x40))
    level[pos + Coord(0,1)] = Tile(Texture(0x2C, (0,0)), Type(0x0D, 0xFF))
    level[pos + Coord(0,2)] = Tile(Texture(0x2C, (0,1)), Type(0x0D, 0xFE))
    level[pos + Coord(0,3)] = Tile(Texture(0x0C, (0,1)), Type(0x0D, 0xFD))

    if size < 2:
        assert False

    if size > 2:
        # Second row (optional + empty)
        level[pos + Coord(1,0)] = Tile(Texture(0x40, (0,0)), Type(0x00, 0x00))
        level[pos + Coord(1,1)] = Tile(Texture(0x60, (0,0)), Type(0x00, 0x00))
        level[pos + Coord(1,2)] = Tile(Texture(0x60, (0,1)), Type(0x00, 0x00))
        level[pos + Coord(1,3)] = Tile(Texture(0x40, (0,1)), Type(0x00, 0x00))

    if size == 4:
        # Third row (optional + empty)
        level[pos + Coord(2,0)] = Tile(Texture(0x41, (0,0)), Type(0x00, 0x00))
        level[pos + Coord(2,1)] = Tile(Texture(0x61, (0,0)), Type(0x00, 0x00))
        level[pos + Coord(2,2)] = Tile(Texture(0x61, (0,1)), Type(0x00, 0x00))
        level[pos + Coord(2,3)] = Tile(Texture(0x41, (0,1)), Type(0x00, 0x00))

    if size > 5:
        assert False

    # Last row, doors
    level[pos + Coord(size-1,0)] = Tile(Texture(0x41, (0,0)), Type(0x09, door_id))
    level[pos + Coord(size-1,1)] = Tile(Texture(0x61, (0,0)), Type(0x09, door_id))
    level[pos + Coord(size-1,2)] = Tile(Texture(0x61, (0,1)), Type(0x09, door_id))
    level[pos + Coord(size-1,3)] = Tile(Texture(0x41, (0,1)), Type(0x09, door_id))


def mk_left_door(level, pos, door_id, size):
    # First row, doors
    level[pos + Coord(0,0)] = Tile(Texture(0x41, (1,0)), Type(0x09, door_id))
    level[pos + Coord(0,1)] = Tile(Texture(0x61, (1,0)), Type(0x09, door_id))
    level[pos + Coord(0,2)] = Tile(Texture(0x61, (1,1)), Type(0x09, door_id))
    level[pos + Coord(0,3)] = Tile(Texture(0x41, (1,1)), Type(0x09, door_id))

    if size < 2:
        assert False

    if size > 2:
        # Second row (optional + empty)
        level[pos + Coord(1,0)] = Tile(Texture(0x41, (1,0)), Type(0x00, 0x00))
        level[pos + Coord(1,1)] = Tile(Texture(0x61, (1,0)), Type(0x00, 0x00))
        level[pos + Coord(1,2)] = Tile(Texture(0x61, (1,1)), Type(0x00, 0x00))
        level[pos + Coord(1,3)] = Tile(Texture(0x41, (1,1)), Type(0x00, 0x00))

    if size == 4:
        # Third row (optional + empty)
        level[pos + Coord(2,0)] = Tile(Texture(0x40, (1,0)), Type(0x00, 0x00))
        level[pos + Coord(2,1)] = Tile(Texture(0x60, (1,0)), Type(0x00, 0x00))
        level[pos + Coord(2,2)] = Tile(Texture(0x60, (1,1)), Type(0x00, 0x00))
        level[pos + Coord(2,3)] = Tile(Texture(0x40, (1,1)), Type(0x00, 0x00))

    if size > 5:
        assert False

    # Last row: shot blocks and h-copies
    level[pos + Coord(size-1,0)] = Tile(Texture(0x0C, (1,0)), Type(0x0C, 0x41))
    level[pos + Coord(size-1,1)] = Tile(Texture(0x2C, (1,0)), Type(0x0D, 0xFF))
    level[pos + Coord(size-1,2)] = Tile(Texture(0x2C, (1,1)), Type(0x0D, 0xFE))
    level[pos + Coord(size-1,3)] = Tile(Texture(0x0C, (1,1)), Type(0x0D, 0xFD))

#TODO: add corners
def level_of_cmap(room, wall_thickness=2):
    # Level has a 16x16 tile for every maptile
    #level = room_dtypes.Level(cmap.dimensions * Coord(16,16))
    cmap = room.cmap
    cmap_rect = Rect(Coord(0,0), cmap.dimensions)
    doors = room.doors
    level = Level(cmap.dimensions.scale(16))
    # Make walls
    for w_pos, tile in cmap.items():
        for direction in tile.walls:
            mk_wall(level, w_pos, direction, wall_thickness)
    # Make Corners
    for pos in cmap_rect:
        if pos not in cmap.tiles:
            for d in coord_directions:
                d90 = Coord(-d.y, d.x)
                diag = d + d90
                if pos+d in cmap.tiles and pos+d90 in cmap.tiles and pos+diag in cmap.tiles:
                    p1 = (pos + diag).scale(16)
                    # Corner square of the correct size
                    r = Rect(p1, p1 + Coord(wall_thickness, wall_thickness))
                    # Now translate it to the correct position
                    px = Coord(0,0)
                    if diag.x < 0:
                        px = Coord(16 - wall_thickness, 0)
                    py = Coord(0,0)
                    if diag.y < 0:
                        py = Coord(0, 16 - wall_thickness)
                    r = r.translate(px + py)
                    mk_default_rect(level, r)
    # Fill tiles outside the map
    for pos in cmap_rect:
        if pos not in cmap.tiles:
            r = Rect(pos, pos+Coord(1,1))
            mk_default_rect(level, r.scale(16))
    # Make doors
    for i, door in enumerate(doors):
        mk_door(level, door.pos - room.pos, door.direction, i)
    # Rest is air
    level.missing_defaults(mk_default_air)
    return level

#
# Conversion to ROM data types
#
#TODO: consider using ROM data types from the start?

def convert_rooms(region_rooms):
    room_header_namef = "room_header_id_{}"
    ids = item_definitions.make_item_definitions()
    # Keeps track of global PLM ids for non-returning PLMs like items
    plm_id = 0
    #TODO: Merge with existing (parsed) ObjNames ?
    # compile_from_savestations will handle the DFS to only compile reachable rooms!
    obj_names = rd.ObjNames()
    # rooms is room_id -> Room
    # Rooms handshake on what to call their headers so that
    # pointers can be created before the room they point to
    #TODO: Save Stations
    # Remember to use names when passing pointer-like values to obj_names.create 
    # (rather than the object itself)
    for region, rooms in region_rooms.items():
        for room_id, room in rooms.items():
            rx, ry = room.level.dimensions
            rid = f"{room.region.name}{room.id}"
            #TODO: FX
            # FX
            #   FXEntry
            #   FX
            fx = obj_names.create(sd.FX, [], None)
            #TODO: enemies
            # Enemy List
            #   Enemies
            enemylist = obj_names.create(sd.EnemyList, [])
            # Enemy Types
            #   EnemyType
            enemytypes = obj_names.create(sd.EnemyTypes, [])
            # PLM List
            #   PLMs
            plms = []
            # Item PLMs
            for item in room.items:
                item_id = int.from_bytes(ids[item.item_type][item.graphic], byteorder="little")
                ix, iy = item.room_pos
                pid = plm_id
                plm_id += 1
                i = obj_names.create(sd.PLM, item_id, ix, iy, pid)
                plms.append(i)
            plmlist = obj_names.create(sd.PLMList, [p.name for p in plms])
            # Level Data
            lbytes = room.level.to_bytes()
            larray = leveldata_utils.level_array_from_bytes(level_bytes, room.level.dimensions)
            level = obj_names.create(sd.LevelData, lbytes, larray, None)
            # Scrolls
            # All green
            #TODO: more nuanced scrolls
            scroll_array = np.zeros((rx // 16, ry // 16))
            for x in range(rx // 16):
                for y in range(ry // 16):
                    scroll_array[x,y] = 2
            scrolls = obj_names.create(sd.Scrolls, scroll_array)
            # Room State
            #TODO: set these extra params
            tilesset = 0
            music_data = 0
            music_track = 0
            layer2_scroll_x = 0
            layer2_scroll_y = 0
            special_xray = 0
            main_asm = 0
            background_index = 0
            setup_asm = 0
            room_state = obj_names.create(sd.RoomState, level_data.name,
                    tileset, music_data, music_track, fx.name, enemylist.name, enemytypes.name,
                    layer2_scroll_x, layer2_scroll_y, scrolls.name, special_xray, main_asm,
                    plmlist.name, background_index, setup_asm)
            # State Chooser
            #   State Choices
            # All rooms are default for now
            statechooser = obj_names.create(sd.StateChooser, [], room_state.name)
            # Door List
            #   Doors
            doors = []
            for door in room.doors:
                #TODO: door.destination is just the ID without the region??
                room_ptr = room_header_namef.format(door.destination)
                d = convert_door(door, room_ptr, obj_names)
                doors.append(d)
            doorlist = obj_names.create(sd.DoorList, [door.name for door in doors])
            # Room Header
            #TODO: calculate from region
            area_index = region.region_id
            map_x, map_y = room.pos
            width, height = room.size
            CRE_bitset = 0 # Refer to rom_tools/rom_data_structures.
            roomheader = sd.RoomHeader(area_index, map_x, map_y, width, height,
                    room.up_scroll, room.down_scroll, CRE_bitset, doorlist.name, statechooser.name)
            obj_names[room_header_namef.format(rid)]
    return obj_names

def convert_door(door, room_ptr, obj_names):
    elevator_properties = 0
    orientation = door.direction
    #TODO: appropriate defaults for orientation
    xlow = 0
    ylow = 0
    xhigh = 0
    yhigh = 0
    dist = 0
    door_asm = None
    door_obj = obj_names.create(sd.Door, room_ptr, elevator_properties, orientation,
            xlow, ylow, xhigh, yhigh, dist, door_asm)
    return door_obj

# Convert a room into a rom RoomHeader for allocation
def convert_room(room):
    level_bytes = room.level.to_bytes()
    # Make a default room state for the room
    # Good luck trying to remember what number goes with what argument!
    s = RoomState(room.room_id, 0, 0xe5e6, 0, 0, room.tileset, room.song, 0, 0, room.bg_scroll, 0, 0, room.bg, 0)
    #TODO

