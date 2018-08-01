from world_rando import concrete_map
from world_rando import item_order_graph
from world_rando import map_gen
from world_rando import map_viz
from world_rando import room_dtypes

from rom_tools import romManager
from encoding import sm_global
import random
import collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def rand_m(p1, p2):
    return concrete_map.manhattan(p1, p2) + random.uniform(0,6)

def less_rand_d(p1, p2):
    return concrete_map.euclidean(p1, p2) + random.uniform(0, 6)

def get_path_info(paths):
    npaths = len(paths)
    lens = [len(p) for p in paths]
    total_length = sum(lens)
    return total_length, npaths

if __name__ == "__main__":
    o, g, rsg, es, ro = item_order_graph.abstract_map()
    cmap = {}
    region_rooms = {}
    ntiles = 0
    room_dims = []
    path_length = 0
    npaths = 0
    for region, graph in rsg.items():
        graph.visualize("output/" + region + "/graph")
        print("Generating map for " + region)
        # Can be as large as 64/32
        dimensions = concrete_map.MCoords(54,30)
        cmap[region], rooms, paths = map_gen.less_naive_gen(dimensions, less_rand_d, graph, es)
        region_rooms[region] = rooms
        ntiles += len(cmap[region])
        for room in rooms.values():
            room_dims.append(len(room))
        l,n = get_path_info(paths)
        path_length += l
        npaths += n

    print("Tiles: " + str(ntiles))
    print("Average room size: " + str(sum(room_dims)/len(room_dims)))
    print("Average path length: " + str(path_length/npaths))
    for region, rcmap in cmap.items():
        map_viz.map_viz(rcmap, "output/" + region + "/cmap.png", "encoding/map_tiles")
    region_room_defs = {region: room_dtypes.room_setup(rooms, cmap[region]) for region, rooms in region_rooms.items()}
    for region, room_defs in region_room_defs.items():
        for room_def in room_defs.values():
            room_def.viz_cmap("output/" + region)

