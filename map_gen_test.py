from world_rando import concrete_map
from world_rando import map_gen
from world_rando import map_viz
from world_rando import item_order_graph
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
    print ro
    print o
    cmap = {}
    ntiles = 0
    room_dims = []
    for region, graph in rsg.items():
        graph.visualize(region)
        print "Generating map for " + region
        cmap[region], rooms = map_gen.less_naive_gen((50, 25), less_rand_d, graph, es)
        ntiles += len(cmap[region])
        for room in rooms.values():
            room_dims.append(len(room))

    print "Tiles: " + str(ntiles)
    for region, rcmap in cmap.items():
        map_viz.map_viz(rcmap, region + ".png", "encoding/map_tiles")

    # compute average room dims
    plt.hist(room_dims)
    plt.savefig("roomdims.png")
    

