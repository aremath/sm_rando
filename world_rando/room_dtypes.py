from .concrete_map import *
from .map_viz import *

class Room(object):

    def __init__(self, cmap, size, room_id, graph=None):
        self.enemies = []
        self.plms = []
        self.graph = graph
        self.cmap = cmap
        self.size = size
        self.room_id = room_id

    def translate(self):
        #produce a Jake room from this
        pass

    def viz_cmap(self, directory):
        fname = directory + "/room" + str(self.room_id) + "_cmap.png"
        map_viz(self.cmap, fname, "encoding/map_tiles")

    def viz_graph(self, directory):
        fname = directory + "/room" + str(self.room_id) + "_graph"
        self.graph.visualize(fname)

#TODO: Door needs to contain some info about what ROOMS it connects, not just what tiles...
# or maybe the tiles on the cmap know what room they are in.
class Door(object):

    def __init__(self, tile1, tile2):
        assert tile2 in tile1.neighbors(), "Tiles are not neighbors!"
        self.direction = tile1.wall_relate(tile2)
        self.tiles = (tile1, tile2)

    def __hash__(self):
        #TODO: is this a valid equivalence relation?
        return hash(self.tiles)

class Tile(object):

    def __init__(self, vtile=None, vflip=None, ptile=None, pflip=None):
        """ vtile is an index into the virtual tile table
            vflip is a (bool, bool) indicating horizontal and vertical flip
            ptile and pflip are the same but for the physical tile table"""
        self.vtile = vtile
        self.vflip = vflip
        self.ptile = ptile
        self.pflip = pflip

    #TODO
    def to_bytes(self):
        pass

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
        room_cmap = cmap.sub(lower, upper + MCoords(1,1))
        size = upper + MCoords(1,1) - lower
        rooms[room_id] = Room(room_cmap, size, room_id)
    return rooms

#TODO: work in progress
# Tile rooms is MCoords -> room#,
# paths is [(start_node, end_node, [MCoord])]
def make_rooms(tile_rooms, paths):
    #TODO: build the rooms first!
    # room_id -> Room
    rooms = {}
    #TODO: node_locs for each node and each door node.
    # room_node_locs: room_id -> node -> MCoords
    for (start, end, path) in paths:
        #TODO: assumes that path starts at start and ends at end
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
        for p in path:
            if tile_rooms[p] != current_room:
                # create a door
                # link the current node with the door
                # set the new current room
                current_room = tile_rooms[p]
        # link the final current node with end
    return rooms

