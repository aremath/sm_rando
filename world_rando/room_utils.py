from sm_rando.world_rando.room_dtypes import *
from sm_rando.world_rando.coord import *
from sm_rando.rom_tools import rom_data_structures

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
    if direction == "U":
        r = Rect(Coord(map_x, map_y), Coord(map_x + 16, map_y + thickness))
    elif direction == "D":
        r = Rect(Coord(map_x, map_y + tstart), Coord(map_x + 16, map_y + 16))
    elif direction == "L":
        r = Rect(Coord(map_x, map_y), Coord(map_x + thickness, map_y + 16))
    elif direction == "R":
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
    if direction == "U":
        add = Coord(6,0)
    elif direction == "D":
        add = Coord(6, 16-size)
    elif direction == "L":
        add = Coord(0, 6)
    elif direction == "R":
        add = Coord(16-size, 6)
    else:
        assert False, "Bad direction: " + str(direction)
    return map_xy_s + add

# Makes a door (default-looking) at the edge of the given maptile
def mk_door(level, map_xy, direction, door_id, size=2):
    p = find_door_pos(map_xy, direction, size)
    if direction == "U":
        door_fun = mk_up_door
    elif direction == "D":
        door_fun = mk_down_door
    elif direction == "L":
        door_fun = mk_left_door
    elif direction == "R":
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

def level_of_cmap(room):
    # Level has a 16x16 tile for every maptile
    #level = room_dtypes.Level(cmap.dimensions * Coord(16,16))
    cmap = room.cmap
    doors = room.doors
    level = Level(cmap.dimensions.scale(16))
    # Make walls
    for w_pos, tile in cmap.items():
        for direction in tile.walls:
            mk_wall(level, w_pos, direction)
    # Make doors
    for door in doors:
        mk_door(level, door.pos - room.pos, door.direction, door.id)
    # Rest is air
    level.missing_defaults(mk_default_air)
    return level

#
# Conversion to ROM data types
#

# Convert a room into a rom RoomHeader for allocation
def convert_room(room):
    level_bytes = room.level.to_bytes()
    # Make a default room state for the room
    # Good luck trying to remember what number goes with what argument!
    s = RoomState(room.room_id, 0, 0xe5e6, 0, 0, room.tileset, room.song, 0, 0, room.bg_scroll, 0, 0, room.bg, 0)
    #TODO

