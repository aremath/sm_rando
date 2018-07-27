from world_rando import concrete_map
from world_rando import item_order_graph
from world_rando import map_gen
from world_rando import map_viz
from world_rando import fixed_cmaps
import random
import collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def rand_m(p1, p2):
    return concrete_map.manhattan(p1, p2) + random.uniform(0,6)

def less_rand_d(p1, p2):
    return concrete_map.euclidean(p1, p2) + random.uniform(0, 6)

if __name__ == "__main__":
    o, g, rsg, es, ro = item_order_graph.abstract_map()
    print(ro)
    print(o)
    cmap = {}
    ntiles = 0
    room_dims = []
    for region, graph in rsg.items():
        graph.visualize("output/a_" + region)
        print("Generating map for " + region)
        dimensions = concrete_map.MCoords(64,32)
        node_locs, node_cmap = map_gen.node_place(graph, dimensions, es[0], es[1])
        cmap[region] = node_cmap

    for region, rcmap in cmap.items():
        map_viz.map_viz(rcmap, "output/" + region + ".png", "encoding/map_tiles")

