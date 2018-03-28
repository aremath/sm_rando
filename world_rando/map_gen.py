from concrete_map import *
#from item_order_graph import *

# just try to re-create the graph
def naive_gen(dimensions, dist, graph, es):

    # build the set of xys
    xys = xy_set(dimensions)

    # make the cmap
    cmap = {}

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
                cmap[xy] = MapTile("")

    room_size = len(cmap) / 2
    random_rooms(room_size, cmap)
    return cmap, len(cmap)

#TODO: generalize this?
# take in node placement 'strategy'
# take in line drawing 'strategy'

def less_naive_gen(dimensions, dist, graph, elevators):
    # first, make the graph
            
    xys = xy_set(dimensions)
    up_es, down_es = elevators

    cmap = {}

    locs = random.sample(xys, graph.nnodes)
    node_list = graph.nodes.keys()
    node_locs = {}
    # choose elevator locations: down elevators are the lowest locs, and up are the highest locs
    #TODO: seems like it doesn't always return the lowest n or highest n points
    sorted_locs = sorted(locs, key=lambda n: n.y)
    up_e_xy = []
    down_e_xy = []
    for node in node_list:
        if node in up_es:
            node_locs[node] = sorted_locs.pop(0) # highest y coordinate is further down
            up_e_xy.append(node_locs[node])
            node_list.remove(node)
        elif node in down_es:
            node_locs[node] = sorted_locs.pop()
            down_e_xy.append(node_locs[node])
            node_list.remove(node)

    random.shuffle(node_list)
    #TODO: need to choose node locations that are not randomly above or below an elevator, or this breaks things
    # -> make an arbitrary random location chooser that respects predicates?
    #TODO: "fixed" boss nodes, and this is where we can make sure there is an item behind Draygon or some such?
    # -> pick an item node later in the order than Draygon and put it past Draygon?
    # -> default to supers
    for i in range(len(node_list)):
        if node_list[i] not in node_locs:
            node_locs[node_list[i]] = sorted_locs[i]

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
            # make a new path to that item from the closest reachable point
            # here, we respect the constraint that nodes along the path can't coincide with an elevator
            offers, finished = map_search(d[0], node_locs[edge.terminal], dist=dist, pred=lambda xy: avoids_elevators(xy, up_e_xy, down_e_xy))
            path = get_path(offers, d[0], node_locs[edge.terminal])
            # make the path into tiles
            #TODO: respect the constraints on the edge
            if path is not None:
                for xy in path:
                    cmap[xy] = MapTile("")

    #TODO: elevators get is_elevator instead of item?
    # every 'interesting' node gets special info
    for node, loc in node_locs.items():
        cmap[loc] = MapTile("")
        if node in up_es:
            cmap[loc].is_elevator = True
            cmap[loc.up()] = MapTile("")
            cmap[loc.up()].is_e_tile = True
        elif node in down_es:
            cmap[loc].is_elevator = True
            cmap[loc.down()] = MapTile("")
            cmap[loc.down()].is_e_tile = True
        else:
            cmap[loc].is_item = True

    # partition the map into random rooms
    #TODO: make sure that an elevator node and its 'is_elevator' are always paired...
    room_size = len(cmap) / 4
    _, rooms = random_rooms(room_size, cmap)
    return cmap, rooms

def xy_set(dimensions):
    xys = set()
    for x in range(dimensions[0]):
        for y in range(dimensions[1]):
            xys.add(MCoords(x,y))
    return xys

def place_nodes(nodes, dimensions, up_es, down_es):
    """Returns a dictionary of node: location by choosing locations for the nodes
     at random."""
    xys = xy_set(dimensions)
    locs = random.sample(xys, graph.nnodes)
    node_list = graph.nodes.keys()
    node_locs = {}
    # choose elevator locations: down elevators are the lowest locs, and up are the highest locs
    #TODO: seems like it doesn't always return the lowest n or highest n points
    sorted_locs = sorted(locs, key = lambda n: n.y)
    up_e_xy = []
    down_e_xy = []
    for node in node_list:
        if node in up_es:
            node_locs[node] = sorted_locs.pop(0) # highest y coordinate is further down
            up_e_xy.append(node_locs[node])
            node_list.remove(node)
        elif node in down_es:
            node_locs[node] = sorted_locs.pop()
            down_e_xy.append(node_locs[node])
            node_list.remove(node)

    random.shuffle(node_list)
    #TODO: need to choose node locations that are not randomly above or below an elevator, or this breaks things
    # -> make an arbitrary random location chooser that respects predicates?
    #TODO: "fixed" boss nodes, and this is where we can make sure there is an item behind Draygon or some such?
    # -> pick an item node later in the order than Draygon and put it past Draygon?
    # -> default to supers
    for i in range(len(node_list)):
        if node_list[i] not in node_locs:
            node_locs[node_list[i]] = sorted_locs[i]
    return node_locs

def avoids_elevators(xy, up_es, down_es):
    """returns if the specified xy isn't above any up elevators
    or below any down elevators. up_es, down_es are the xy lists of
    up and down elevators"""
    return (not is_p_list(xy, up_es, is_above)) and (not is_p_list(xy, down_es, is_below))

def test(x, n):
    return True
