from .room_dtypes import *
from .room_utils import *
from .coord import *

# Room Generation:

# takes d: a -> [b] to
# b -> a, assuming distinct b
def reverse_list_dict(d):
    reverse = {}
    for (k, vl) in d.items():
        for v in vl:
            reverse[v] = k
    return reverse

# Room tiles is room_id -> [MCoord]
def room_setup(room_tiles, cmap):
    rooms = {}
    for room_id, coord_set in room_tiles.items():
        lower, upper = extent(coord_set)
        room_cmap, room_pos = cmap.sub(lower, upper + Coord(1,1))
        size = upper + Coord(1,1) - lower
        rooms[room_id] = Room(room_cmap, size, room_id, room_pos)
    return rooms

#TODO: work in progress
# Tile rooms is Coord -> room#,
# paths is [(start_node, end_node, [MCoord])]
# rooms is room_id -> room
def room_graphs(rooms, tile_rooms, paths):
    #TODO: node_locs for each node and each door node.
    # room_node_locs: room_id -> node -> Coord
    for (start, end, path) in paths:
        room_start = tile_rooms[path[0]]
        room_end = tile_rooms[path[-1]]
        gstart = rooms[room_start].graph
        if start not in gstart.nodes:
            gstart.add_node(start)
        gend = rooms[room_end].graph
        if end not in gend.nodes:
            gend.add_node(end)
        current_room = room_start
        current_node = start
        current_pos = path[0]
        for new_pos in path:
            new_room = tile_rooms[new_pos]
            if new_room != current_room:
                gcurrent = rooms[current_room].graph
                gnew = rooms[new_room].graph
                # Create a door
                # Node in the old room
                current_wr = current_pos.wall_relate(new_pos)
                current_door = str(current_room) + "_" + str(current_pos) + "_" + current_wr
                if current_door not in gcurrent.nodes:
                    gcurrent.add_node(current_door)
                    # Create a new door for current -> new
                    d = rooms[current_room].doors
                    d.append(Door(current_pos, current_wr, current_room, new_room, len(d)))
                # Link the current node with the door
                gcurrent.update_edge(current_node, current_door)
                # Node in the new room
                new_wr = new_pos.wall_relate(current_pos)
                new_door = str(new_room) + "_" + str(new_pos) + "_" + new_wr
                if new_door not in gnew.nodes:
                    gnew.add_node(new_door)
                    # Create a new door for the new -> current
                    d = rooms[new_room].doors
                    d.append(Door(new_pos, new_wr, new_room, current_room, len(d)))
                # set the new current room
                current_room = tile_rooms[new_pos]
                # the new current node is the door we came into the new room by
                current_node = new_door
            current_pos = new_pos
        # link the final current node with end
        gend.update_edge(current_node, end)

def make_rooms(room_tiles, cmap, paths):
    rooms = room_setup(room_tiles, cmap)
    tile_rooms = reverse_list_dict(room_tiles)
    room_graphs(rooms, tile_rooms, paths)
    # ... generate map data etc ...
    for r in rooms.values():
        r.level_data = level_of_cmap(r)
    return rooms

#TODO
#
def miniroom_partition(room_def, max_parts):
    """Creates a partition of the room into minirooms.
    The partition is a list of sets of xy values that index
    into the room dictionary."""
    #TODO: a list of xys isn't that useful to know the min and the max...
    while True:
        # choose a partition to subdivide
        # choose an x or a y to subdivide it at
        # break if the xy is invalid
        #   - causes a partition area to be too small
        #   - goes through an obstacle like a door
        #   - creates a partition over the max
        break
    pass

# Translates the (uncompressed) leveldata bytes to a level dictionary.
# levelsize is the number of bytes in the decompressed level1 data
# = 2 * the number of BTS bytes
# = the number of level2 bytes
def level_from_bytes(levelbytes, dimensions):
    # First two bytes are the amount of level1 data
    levelsize = int.from_bytes(levelbytes[0:2], byteorder='little')
    # Cut off the size
    levelbytes = levelbytes[2:]
    # Make sure everything matches
    assert levelsize % 2 == 0, "Purported level size is not even length"
    assert levelsize == dimensions.x * dimensions.y * 2, "Level data length does not match specified room dimensions"
    # The level might not include level2 data
    if len(levelbytes) == int(2.5 * levelsize):
        has_level2 = True
    elif len(levelbytes) == int(1.5 * levelsize):
        has_level2 = False
    else:
        assert False, "Purported level size does not match actual level size"
    level = Level(dimensions)
    for y in range(dimensions.y):
        for x in range(dimensions.x):
            index = y * dimensions.x + x
            level1index = index * 2
            level1 = int.from_bytes(levelbytes[level1index:level1index+2], byteorder='little')
            btsindex = index + levelsize
            bts = int.from_bytes(levelbytes[btsindex:btsindex+1], byteorder='little')
            if has_level2:
                level2index = index + (3*levelsize/2)
                level2 = int.from_bytes(levelbytes[level2index:level2index+2], byteorder='little')
            else:
                level2 = 0
            #TODO: level2 info dropped on the floor
            
            ttype = level1 >> 12
            hflip = (level1 >> 10) & 1
            vflip = (level1 >> 11) & 1
            tindex = level1 & 0b1111111111
            texture = Texture(tindex, (hflip, vflip))
            tiletype = Type(ttype, bts)
            level[Coord(x,y)] = Tile(texture, tiletype)
    return level
