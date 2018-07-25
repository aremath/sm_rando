from .concrete_map import *

#TODO: Bounds checking on the results of the spring model
#TODO: A way to keep the model going until the average absolute spring force falls below a threshold?
#TODO: This can break the way elevators are chosen...
def spring_model(node_locs, graph, n_iterations, spring_constant, spring_equilibrium, dt):
    """Changes node placement based on a simple spring model.
    Node locs is the dictionary of initial node placements and is edited by the function.
    graph is the graph of how the  nodes are connected to each other
        (i.e. where to place springs).
    n_iterations is how many time steps to run the model for.
        A few should suffice for my purposes.
    spring_constant is the k in -kx.
    spring_equilibrium is the distance where the spring is at rest.
    dt is the time step.
    Doesn't return anything, but changes node_locs to a (hopefully) 
    lower-energy configuration."""
    # node locs is node_name -> node_position
    # node_name -> node_velocity
    # using mcoords as a vector
    node_v = { n : MCoords(0,0) for n in node_locs }
    # node_name -> node_acceleration
    node_a = { n : MCoords(0,0) for n in node_locs }
    iteration = 0
    while iteration < n_iterations:
        for n in node_locs:
            # update node_a
            for e in graph.nodes[n].edges:
                t = e.terminal
                # the amount of stretching, possibly negative
                x = euclidean(node_locs[n], node_locs[t]) - spring_equilibrium
                # direction
                direction = (node_locs[n] - node_locs[t]).to_unit()
                #-kx
                # TODO: Should be -?
                node_a[t] = node_a[t] + direction.scale(spring_constant * x)
            # update node_v
            node_v[n] = node_v[n] + node_a[n].scale(dt)
            # update node_locs
            node_locs[n] = node_locs[n] + node_v[n].scale(dt)
        iteration = iteration + 1
    # resolve to an int
    # TODO: is there a dict map function?
    node_locs = { n: node_locs[n].resolve_int() for n in node_locs }
    return node_locs

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
                cmap[xy] = MapTile()

    room_size = len(cmap) / 2
    cmap.random_rooms(room_size)
    return cmap, len(cmap)

#TODO: generalize this?
# take in node placement 'strategy'
# take in line drawing 'strategy'
#TODO: add save points!

def less_naive_gen(dimensions, dist, graph, elevators):
    # first, make the graph
            
    xys = xy_set(dimensions)
    up_es, down_es = elevators

    cmap = ConcreteMap(dimensions)

    locs = random.sample(xys, graph.nnodes)
    node_list = graph.nodes.keys()
    node_locs = {}
    # choose elevator locations: down elevators are the lowest locs, and up are the highest locs
    sorted_locs = sorted(locs, key=lambda n: n.y)
    up_e_xy = []
    down_e_xy = []
    for node in node_list:
        if node in up_es:
            node_locs[node] = sorted_locs.pop(0) # highest y coordinate is further down
            up_e_xy.append(node_locs[node])
        elif node in down_es:
            node_locs[node] = sorted_locs.pop()
            down_e_xy.append(node_locs[node])
    # remove the elevators from the list to choose locs for the rest of the nodes
    node_list = list(set(node_list) - up_es - down_es)

    random.shuffle(node_list)
    #TODO: need to choose node locations that are not randomly above or below an elevator, or this breaks things
    # -> make an arbitrary random location chooser that respects predicates?
    #TODO: "fixed" boss nodes, and this is where we can make sure there is an item behind Draygon or some such?
    # -> pick an item node later in the order than Draygon and put it past Draygon?
    # -> default to supers
    for i in range(len(node_list)):
        if node_list[i] not in node_locs:
            node_locs[node_list[i]] = sorted_locs[i]

    # TODO: fiddle with the constants
    # Run the spring model to lower the total "energy" of the graph:
    # make it smaller in a sensible way.
    # TODO: How to avoid collisions?
    # TODO: Right now, the above_elevators predicate is created before this decides
    # where the elevators will actually live.
    #print(node_locs)
    node_locs = spring_model(node_locs, graph, 5, 1, 3, 0.1)
    #print(node_locs)

    rnodes = list(graph.nodes.keys())
    random.shuffle(rnodes)
    for node in rnodes:
        for edge in graph.nodes[node].edges:
            # path from n1 to n2
            # first, find all nodes reachable from n1 that are already placed
            o, f = cmap.map_bfs(node_locs[node], None, reach_pred = lambda x: x in cmap)
            # find the closest.
            #TODO: euclidean?
            dists = [(p, euclidean(p, node_locs[edge.terminal])) for p in list(f)]
            dists = sorted(dists, key = lambda n: n[1])
            #TODO: probability distribution over dists?
            d = dists[0]
            #TODO: if d == node_locs[edge.terminal] -> no need for a path
            # make a new path to that item from the closest reachable point
            # here, we respect the constraint that nodes along the path can't coincide with an elevator
            offers, finished = cmap.map_search(d[0], node_locs[edge.terminal], dist=dist, reach_pred=lambda xy: avoids_elevators(xy, up_e_xy, down_e_xy))
            path = get_path(offers, d[0], node_locs[edge.terminal])
            # make the path into tiles
            #TODO: respect the constraints on the edge
            if path is not None:
                for xy in path:
                    cmap[xy] = MapTile()
            #TODO: if path is None: what?

    #TODO: elevators get is_elevator instead of item?
    # every 'interesting' node gets special info
    for node, loc in node_locs.items():
        cmap[loc] = MapTile()
        if node in up_es:
            cmap[loc].tile_type = TileType.elevator_main_up
            cmap[loc.up()] = MapTile(_tile_type=TileType.elevator_shaft)
        elif node in down_es:
            cmap[loc].tile_type = TileType.elevator_main_down
            cmap[loc.down()] = MapTile(_tile_type=TileType.elevator_shaft)
        else:
            cmap[loc].is_item = True

    # partition the map into random rooms
    #TODO: make sure that an elevator node and its 'is_elevator' are always paired...
    room_size = len(cmap) // 4
    _, rooms = cmap.random_rooms(room_size)
    return cmap, rooms

# Creates space of MCoords from 0 to dimensions not including the upper bound
def xy_set(dimensions):
    xys = set()
    for x in range(dimensions.x):
        for y in range(dimensions.y):
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

def connecting_path(cmap, t1, t2, threshold):
    """creates a path from t1 to t2 if
    bfs_d(t1, t2) / d(t1, t2) exceeds threshold."""
    assert t1 in cmap, str(t1) + " not in cmap."
    assert t2 in cmap, str(t1) + " not in cmap."
    assert not cmap[t1].is_fixed
    assert not cmap[t2].is_fixed
    o, f = cmap.map_bfs(t1, lambda x: x == t2, reach_pred=lambda x: x in cmap and not cmap[x].is_fixed)
    p = get_path(o, t1, t2)
    ratio = len(p) / euclidean(t1, t2) + 1e-5 # epsilon for nonzero

# Want to search for a location that satisfies the properties:
#   - In_Bounds - Within the bounded area allowed for the map
#               And placing the pattern here respects the bounds
#   - Can_Place - None of the fixed tiles in the submap we are placing overlap with any already-placed tiles
#   - Avoids_Elevators - As above, but only respecting elevators that have already been placed
# One way of achieving avoids_elevators is just to "fix" every square above or 
# below an elevator when placing it. Then make elevators look for squares where they're not above
# (or below) any already-placed square. (And for ease, perhaps place the elevators first)

