from .coord import *
from .concrete_map import *
from . import fixed_cmaps

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
    Returns a lower potential-energy node_locs."""
    # node locs is node_name -> node_position
    # node_name -> node_velocity
    # using mcoords as a vector
    node_v = { n : Coord(0,0) for n in node_locs }
    # node_name -> node_acceleration
    node_a = { n : Coord(0,0) for n in node_locs }
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

#TODO: generalize this?
# take in node placement 'strategy'
# take in line drawing 'strategy'
#TODO: add save points!
#TODO:
# -> pick an item node later in the order than Draygon and put it past Draygon?
# -> default to supers
#TODO: Possibly just add some extra edges to the regional graph to make it more "uniform"
# through the spring model?

def less_naive_gen(dimensions, dist, graph, elevators):
    r = Rect(Coord(0,0), dimensions)
    xys = r.as_set()
    up_es, down_es = elevators
    # Find a placement for nodes, and initialize it with the areas for those nodes
    node_locs, cmap, bboxes = node_place(graph, dimensions, up_es, down_es)

    rnodes = list(graph.nodes.keys())
    random.shuffle(rnodes)
    # Holds all the paths, along with their constraints (TODO: the constraints)
    paths = []
    for node in rnodes:
        for edge in graph.nodes[node].edges:
            # Special case - edges from MB start from the escape point!
            if node == "Mother_Brain":
                start_point = node_locs[node] + Coord(-5,0)
            else:
                start_point = node_locs[node]
            end_point = node_locs[edge.terminal]
            # path from n1 to n2
            # first, find all nodes reachable from n1 that are already placed
            _, o, f = cmap.map_bfs(start_point, None, reach_pred = lambda x: cmap.step_on(x))
            # find the closest.
            dists = [(p, euclidean(p, node_locs[edge.terminal])) for p in list(f)]
            dists = sorted(dists, key = lambda n: n[1])
            #TODO: probability distribution over dists?
            closest, _ = dists[0]
            # Find the path to closest
            to_closest = get_path(o, start_point, closest)
            # make a new path to that item from the closest reachable point
            offers, finished = cmap.map_search(closest, end_point,
                dist=dist, reach_pred= lambda x: cmap.can_place(x))
            to_end = get_path(offers, closest, node_locs[edge.terminal])
            # make the path into tiles
            #TODO: respect the constraints on the edge
            if to_end is not None:
                for xy in to_end:
                    if xy not in cmap:
                        cmap[xy] = MapTile()
            else:
                assert False, "Cannot find path: " + str(closest) + ", " + str(node_locs[edge.terminal])
            path = path_concat(to_closest, to_end)
            paths.append((node, edge.terminal, path))
    # partition the map into random rooms
    room_size = len(cmap) // 5
    #_, rooms = cmap.random_rooms(room_size)
    rooms = cmap.random_rooms_alt(room_size, bboxes)
    #TODO: Each room grabs the map tiles that are inside its bounding box!
    #TODO: Or could use a budgeted cellular automaton to fill in "corner" spaces with map tiles...
    return cmap, rooms, paths

def random_node_place(graph, dimensions, up_es, down_es):
    """Returns a dictionary of node -> location by choosing locations for the nodes
    at random."""
    r = Rect(Coord(0,0), dimensions)
    xys = r.as_set()
    locs = random.sample(xys, graph.nnodes)
    node_list = graph.nodes.keys()
    node_locs = {}
    # choose elevator locations: down elevators are the lowest locs, and up are the highest locs
    #TODO: seems like it doesn't always return the lowest n or highest n points
    sorted_locs = sorted(locs, key = lambda n: n.y)
    for node in node_list:
        if node in up_es:
            node_locs[node] = sorted_locs.pop(0) # highest y coordinate is further down
        elif node in down_es:
            node_locs[node] = sorted_locs.pop()
    node_list = list(set(node_list) - up_es - down_es)

    random.shuffle(node_list)
    #TODO: this is where we can make sure there is an item behind Draygon or some such??
    # -> pick an item node later in the order than Draygon and put it past Draygon?
    # -> default to supers
    for i in range(len(node_list)):
        if node_list[i] not in node_locs:
            node_locs[node_list[i]] = sorted_locs[i]
    return node_locs

# Area_maker is position -> cmap, bounding_box (optional)
# intended for use with fixed_cmaps.mk_area() where area, and dims are known.
# True if the cmap generated by area_maker(pos) is valid, and can be composed with cmap.
def can_place(area_maker, pos, cmap):
    node_cmap = area_maker(pos)
    if node_cmap is not None:
        if cmap.compose(node_cmap, collision_policy="none") is not None:
            return True
        else:
            return False
    else:
        return False

# Find a placement of the nodes that allows their concrete maps to co-exist within
# the boundaries of cmap.
# Initial is a node_locs: node : location. cmap is a ConcreteMap. areas is node : (pos -> cmap)
def find_placement(initial, areas, infos, cmap):
    dimensions = cmap.dimensions
    final_node_locs = {}
    bboxes = []
    for node, init_pos in initial.items():
        node_area_maker = lambda p: fixed_cmaps.mk_area(p, dimensions, areas(node))
        g, _, _ = cmap.map_bfs(init_pos, lambda p: can_place(node_area_maker, p, cmap))
        assert g is not None, "No valid place found."
        final_node_locs[node] = g
        # Actually place it into the map
        i_cmap, i_bboxes = infos(node, g, dimensions)
        cmap = cmap.compose(i_cmap)
        bboxes.extend(i_bboxes)
    return final_node_locs, cmap, bboxes

# Find a placement for nodes where their respective areas do not violate
# each other.
#   Random initially, with elevators guaranteed to be at the top and bottom (initially)
#   Subjected to a spring model which reduces the total potential energy (moves far nodes closer)
#   Subject to a search so that nodes can be placed without violating each other's areas.
def node_place(graph, dimensions, up_es, down_es):
    initial = random_node_place(graph, dimensions, up_es, down_es)
    spring = spring_model(initial, graph, 5, 2, 3, 0.1)
    trunc_spring = {n : xy.truncate(Coord(0,0), dimensions) for (n, xy) in spring.items()}
    # Now do a search for a good placement for each nod.
    cmap = ConcreteMap(dimensions)
    areas = lambda n: fixed_cmaps.node_to_area(n, up_es, down_es)
    infos = lambda n,p,d: fixed_cmaps.node_to_info(n, p, d, up_es, down_es)
    return find_placement(trunc_spring, areas, infos, cmap)

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
    _, o, f = cmap.map_bfs(t1, lambda x: x == t2, reach_pred=lambda x: x in cmap and not cmap[x].is_fixed)
    p = get_path(o, t1, t2)
    ratio = len(p) / euclidean(t1, t2) + 1e-5 # epsilon for nonzero

