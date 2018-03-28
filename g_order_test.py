from world_rando.item_order_graph import *
from encoding import sm_global

if __name__ == "__main__":
    o, g = order_graph()
    print o
    ro, rf = partition_order(g, sm_global.regions)
    print rf
    es = make_elevators(g, rf)
    r_s = region_subgraphs(g, rf)
    for r, sg in r_s.items():
        sg.visualize(r)
    g.visualize("all")

