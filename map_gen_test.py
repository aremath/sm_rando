from world_rando import concrete_map
from world_rando import map_gen
from world_rando import map_viz
from world_rando import item_order_graph
import random

def rand_m(p1, p2):
    return concrete_map.manhattan(p1, p2) + random.uniform(0,6)

def less_rand_d(p1, p2):
    return concrete_map.euclidean(p1, p2) + random.uniform(0, 6)

if __name__ == "__main__":
    o, g, rsg = item_order_graph.abstract_map()
    print o
    cmap = {}
    ntiles = 0
    for region, graph in rsg.items():
        cmap[region], n = map_gen.less_naive_gen((50, 25), less_rand_d, graph)
        ntiles += n

    print "Tiles: " + str(ntiles)
    for region, rcmap in cmap.items():
        map_viz.map_viz(rcmap, region + ".png", "encoding/map_tiles")
    #cmap = map_gen.less_naive_gen((100, 50), less_rand_d) #concrete_map.rand_d
    #map_viz.map_viz(cmap, "E", "map.png", "encoding/map_tiles")
