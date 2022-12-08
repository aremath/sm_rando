from world_rando import concrete_map
from world_rando import item_order_graph
from world_rando import map_gen
from world_rando import map_viz
from world_rando import room_gen
from world_rando.room_dtypes import convert_rooms

from rom_tools import rom_manager
from encoding import sm_global
import random
import collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

#TODO: CMapInfo, RoomInfo, etc object types to make it easier to add to and refer to info

def get_path_info(paths):
    npaths = len(paths)
    lens = [len(p.coord_path) for p in paths]
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

def generate_abstract_map(settings):
    return item_order_graph.abstract_map(settings.abstract_map_settings, settings.global_settings)

def generate_concrete_map(settings, abstract_map_info):
    o, g, rsg, ro = abstract_map_info
    region_cmaps = {}
    region_rooms = {}
    region_paths = {}
    region_room_defs = {}
    region_node_info = {}
    ntiles = 0
    room_dims = []
    path_length = 0
    npaths = 0
    for region, graph in rsg.items():
        print(f"Generating map for {region}")
        cmap, rooms, paths, node_info = map_gen.map_gen(region.size, graph, settings.concrete_map_settings)
        region_cmaps[region] = cmap
        region_rooms[region] = rooms
        region_paths[region] = paths
        region_node_info[region] = node_info
        # Accumulate Diagnostic / Aggregate info
        ntiles += len(region_cmaps[region])
        for room in rooms.values():
            room_dims.append(len(room))
        l,n = get_path_info(paths)
        path_length += l
        npaths += n
    extra_info = (npaths, path_length, ntiles, room_dims)
    return region_cmaps, region_rooms, region_paths, region_node_info, extra_info

def generate_rooms(settings, concrete_map_info):
    region_cmaps, region_rooms, region_paths, region_node_info, _ = concrete_map_info
    region_room_defs = {}
    for region in region_cmaps.keys():
        print(f"Generating rooms for {region}")
        cmap = region_cmaps[region]
        rooms = region_rooms[region]
        paths = region_paths[region]
        node_info = region_node_info[region]
        region_room_defs[region] = room_gen.make_rooms(rooms, cmap, paths, node_info, region, settings.room_gen_settings, settings.output_settings)
    return region_room_defs

def reify_rooms(room_info, parsed_rooms):
    print("Converting Rooms to ROM format")
    rooms = []
    # Collect the rooms
    for room_d in room_info.values():
        for room in room_d.values():
            rooms.append(room)
    return convert_rooms(rooms, parsed_rooms)

def visualize_abstract_maps(settings, abstract_map_info):
    _, g, rsg, _ = abstract_map_info
    # Visualize the overall graph
    g.visualize("output/graph")
    # Visualize the individual region graphs
    for region, graph in rsg.items():
        graph.visualize(f"output/{region.name}/graph")

def visualize_concrete_maps(out_settings, concrete_map_info):
    out_f = out_settings["output"]
    region_cmaps, _, _, _, _ = concrete_map_info
    for region, rcmap in region_cmaps.items():
        map_viz.map_viz(rcmap, f"{out_f}/{region.name}/cmap.png", out_settings["map_tiles"])

def mission_embeddings(settings, concrete_map_info, abstract_map_info):
    order, _, _, _ = abstract_map_info
    region_cmaps, _, region_paths, _, _ = concrete_map_info
    for region, rcmap in region_cmaps.items():
        print(f"Embedding for {region}")
        paths = region_paths[region]
        fname = f"output/{region.name}/mission_embedding.png"
        map_viz.mission_embedding(rcmap, paths, order, fname)

def visualize_rooms(out_settings, room_info):
    out_f = out_settings["output"]
    for region, room_defs in room_info.items():
        for room_def in room_defs.values():
            if not isinstance(room_def.level, str):
                outstr = f"{out_f}/{region.name}"
                room_def.viz_cmap(outstr, out_settings["map_tiles"])
                room_def.viz_graph(outstr)
                room_def.viz_level(outstr, out_settings["room_tiles"])
