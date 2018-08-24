from .concrete_map import *
from .map_viz import *
from data_types import basicgraph

class Room(object):

    def __init__(self, cmap, size, room_id, graph=None):
        self.enemies = []
        self.plms = []
        if graph is None:
            self.graph = basicgraph.BasicGraph()
        else:
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
# rooms is room_id -> room
def room_graphs(rooms, tile_rooms, paths):
    #TODO: node_locs for each node and each door node.
    # room_node_locs: room_id -> node -> MCoords
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
                # Link the current node with the door
                gcurrent.update_edge(current_node, current_door)
                # Node in the new room
                new_wr = new_pos.wall_relate(current_pos)
                new_door = str(new_room) + "_" + str(new_pos) + "_" + new_wr
                if new_door not in gnew.nodes:
                    gnew.add_node(new_door)
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
    return rooms

