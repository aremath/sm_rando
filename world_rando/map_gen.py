from concrete_map import *
from item_order_graph import *

# just try to re-create the graph
def naive_gen(dimensions, dist):
    # first, make the abstract map
    order, g = order_graph()

    # build the set of xys
    xys = xy_set(dimensions)

    # make the cmap
    cmap = {}
    cmap["E"] = {} # for now, one region TODO

    # generate a map!
    # first, choose locations for each node
    locs = random.sample(xys, g.nnodes)
    node_list = g.nodes.keys()
    node_locs = {}
    for i in range(len(node_list)):
        node_locs[node_list[i]] = locs[i]

    # now put a path for each edge
    for node in g.nodes:
        for edge in g.nodes[node].edges:
            offers, finished = map_search(node_locs[node], node_locs[edge.terminal], dist=dist)
            path = get_path(offers, node_locs[node], node_locs[edge.terminal])
            for xy in path:
                cmap["E"][xy] = MapTile("")

    room_size = len(cmap["E"]) / 2
    print len(cmap["E"])
    random_rooms(room_size, cmap, "E")

    return cmap

def less_naive_gen(dimensions, dist):
    # first, make the graph
    order, g = order_graph()
            
    xys = xy_set(dimensions)

    cmap = {}
    cmap["E"] = {}

    locs = random.sample(xys, g.nnodes)
    node_list = g.nodes.keys()
    node_locs = {}
    for i in range(len(node_list)):
        node_locs[node_list[i]] = locs[i]

    for node in g.nodes:
        for edge in g.nodes[node].edges:
            # path from n1 to n2
            # first, find all nodes reachable from n1
            o, f = map_bfs(node_locs[node], None, pred = lambda x: x in cmap["E"])
            # find the closest.
            #TODO: euclidean?
            dists = [(p, euclidean(p, node_locs[edge.terminal])) for p in list(f)]
            dists = sorted(dists, key = lambda n: n[1])
            #TODO: probability distribution over dists?
            d = dists[0]
            offers, finished = map_search(d[0], node_locs[edge.terminal], dist=dist)
            path = get_path(offers, d[0], node_locs[edge.terminal])
            if path is not None:
                for xy in path:
                    cmap["E"][xy] = MapTile("")

    for loc in node_locs.values():
        cmap["E"][loc] = MapTile("")
        cmap["E"][loc].is_item = True

    room_size = len(cmap["E"]) / 3
    print len(cmap["E"])
    random_rooms(room_size, cmap, "E")

    return cmap

def xy_set(dimensions):
    xys = set()
    for x in range(dimensions[0]):
        for y in range(dimensions[1]):
            xys.add(MCoords(x,y))
    return xys
