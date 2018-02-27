from concrete_map import *
#from item_order_graph import *

# just try to re-create the graph
def naive_gen(dimensions, dist, region, graph, cmap):

    # build the set of xys
    xys = xy_set(dimensions)

    # make the cmap
    cmap[region] = {}

    # generate a map!
    # first, choose locations for each node
    locs = random.sample(xys, graph.nnodes)
    node_list = graph.nodes.keys()
    node_locs = {}
    for i in range(len(node_list)):
        node_locs[node_list[i]] = locs[i]

    # now put a path for each edge
    for node in graph.nodes:
        for edge in graph.nodes[node].edges:
            offers, finished = map_search(node_locs[node], node_locs[edge.terminal], dist=dist)
            path = get_path(offers, node_locs[node], node_locs[edge.terminal])
            for xy in path:
                cmap[region][xy] = MapTile("")

    room_size = len(cmap[region]) / 2
    random_rooms(room_size, cmap, region)
    return cmap, len(cmap)

def less_naive_gen(dimensions, dist, graph):
    # first, make the graph
            
    xys = xy_set(dimensions)

    cmap = {}

    locs = random.sample(xys, graph.nnodes)
    node_list = graph.nodes.keys()
    node_locs = {}
    for i in range(len(node_list)):
        node_locs[node_list[i]] = locs[i]

    for node in graph.nodes:
        for edge in graph.nodes[node].edges:
            # path from n1 to n2
            # first, find all nodes reachable from n1
            o, f = map_bfs(node_locs[node], None, pred = lambda x: x in cmap)
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
                    cmap[xy] = MapTile("")

    for loc in node_locs.values():
        cmap[loc] = MapTile("")
        cmap[loc].is_item = True

    room_size = len(cmap) / 3
    random_rooms(room_size, cmap)
    return cmap, len(cmap)

def xy_set(dimensions):
    xys = set()
    for x in range(dimensions[0]):
        for y in range(dimensions[1]):
            xys.add(MCoords(x,y))
    return xys
