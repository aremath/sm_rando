from sm_rando.world_rando import concrete_map
from sm_rando.world_rando import item_order_graph
from sm_rando.world_rando import map_gen
from sm_rando.world_rando import map_viz
from sm_rando.world_rando import room_gen
from sm_rando.world_rando import settings
from sm_rando.world_rando import pattern

from rom_tools import rom_manager
from encoding import sm_global
import random
import collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

#TODO: config file for editing settings so that it's easier to change the settings.

def get_path_info(paths):
    npaths = len(paths)
    lens = [len(p[2]) for p in paths]
    total_length = sum(lens)
    return total_length, npaths

def print_stats(extra_info):
    npaths, path_length, ntiles, room_dims = extra_info
    print("Tiles: " + str(ntiles))
    print("Average room size: " + str(sum(room_dims)/len(room_dims)))
    print("Average path length: " + str(path_length/npaths))

def plot_room_dims(room_dims):
    plt.hist(room_dims)
    plt.savefig("output/roomdims.png")

def generate_abstract_map():
    return item_order_graph.abstract_map(settings.abstract_map_settings)

def generate_concrete_map(abstract_map_info):
    o, g, rsg, es, ro = abstract_map_info
    region_cmaps = {}
    region_rooms = {}
    region_paths = {}
    region_room_defs = {}
    ntiles = 0
    room_dims = []
    path_length = 0
    npaths = 0
    for region, graph in rsg.items():
        print("Generating map for " + region)
        # At most 64,32
        dimensions = concrete_map.Coord(54,30)
        cmap, rooms, paths = map_gen.map_gen(dimensions, graph, es, settings.concrete_map_settings)
        region_cmaps[region] = cmap
        region_rooms[region] = rooms
        region_paths[region] = paths
        # Accumulate Diagnostic / Aggregate info
        ntiles += len(region_cmaps[region])
        for room in rooms.values():
            room_dims.append(len(room))
        l,n = get_path_info(paths)
        path_length += l
        npaths += n
    extra_info = (npaths, path_length, ntiles, room_dims)
    return region_cmaps, region_rooms, region_paths, extra_info

def generate_rooms(concrete_map_info):
    patterns = pattern.load_patterns("encoding/patterns")
    region_cmaps, region_rooms, region_paths, _ = concrete_map_info
    region_room_defs = {}
    for region in region_cmaps.keys():
        cmap = region_cmaps[region]
        rooms = region_rooms[region]
        paths = region_paths[region]
        region_room_defs[region] = room_gen.make_rooms(rooms, cmap, paths, settings.room_gen_settings, patterns)
    return region_room_defs

def visualize_abstract_maps(abstract_map_info):
    _, g, rsg, _, _ = abstract_map_info
    # Visualize the overall graph
    g.visualize("output/graph")
    # Visualize the individual region graphs
    for region, graph in rsg.items():
        graph.visualize("output/" + region + "/graph")

def visualize_concrete_maps(concrete_map_info):
    region_cmaps, _, _, _ = concrete_map_info
    for region, rcmap in region_cmaps.items():
        map_viz.map_viz(rcmap, "output/" + region + "/cmap.png", "encoding/map_tiles")

def visualize_rooms(room_info):
    for region, room_defs in room_info.items():
        for room_def in room_defs.values():
            room_def.viz_cmap("output/" + region)
            room_def.viz_graph("output/" + region)
            room_def.viz_level("output/" + region)
