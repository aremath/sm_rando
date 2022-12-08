import random
from typing import Dict, Set, Tuple

from world_rando.coord import Coord, Rect
from world_rando.concrete_map import Path, ConcreteMap, MapTile, get_path, euclidean, path_concat
from world_rando import fixed_cmaps
from world_rando import map_viz
from world_rando.item_order_graph import NodeType

#TODO: Bounds checking on the results of the spring model
#TODO: A way to keep the model going until the average absolute spring force falls below a threshold?
#TODO: This can break the way elevators are chosen...
#TODO: damping!
def spring_model(node_locs, graph, n_iterations, spring_constant, spring_equilibrium, dt, damping):
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
    node_v = {n : Coord(0, 0) for n in node_locs}
    # node_name -> node_acceleration
    node_a = {n : Coord(0, 0) for n in node_locs}
    iteration = 0
    while iteration < n_iterations:
        for n in node_locs:
            # Update node_v
            for e in graph.nodes[n].edges:
                t = e.terminal
                # The amount of stretching, possibly negative
                x = euclidean(node_locs[n], node_locs[t]) - spring_equilibrium
                # Direction
                n_to_t = (node_locs[t] - node_locs[n]).to_unit()
                #-kx
                node_v[n] = node_v[n] + n_to_t.scale(spring_constant * x * dt)
                node_v[t] = node_v[t] + n_to_t.scale(-spring_constant * x * dt)
            # update node_locs
            node_locs[n] = node_locs[n] + node_v[n].scale(dt)
        iteration = iteration + 1
    # resolve to an int
    # TODO: is there a dict map function?
    node_locs = {n: node_locs[n].resolve_int() for n in node_locs}
    return node_locs

#TODO: generalize this?
# take in node placement 'strategy'
# take in line drawing 'strategy'
#TODO: add save points!
#TODO:
# -> pick an item node later in the order than Draygon and put it past Draygon?
# -> default to supers
# OR a map station after every boss?
#TODO: Possibly just add some extra edges to the regional graph to make it more "uniform"
# through the spring model?
#TODO: Make map generation less dependent on defined region size!
#   A map with few nodes and a large region size should be small.
#   A map with many nodes and a small region size should fill the region.

def map_gen(dimensions, graph, settings):
    """
    Generate a concrete graph
    """
    dist = settings["distance_metric"]
    up_es = set([n for n in graph.nodes if graph.nodes[n].data == NodeType.ELEVATOR_UP])
    down_es = set([n for n in graph.nodes if graph.nodes[n].data == NodeType.ELEVATOR_DOWN])
    # Find a placement for nodes, and initialize it with the areas for those nodes
    node_locs, cmap, bboxes = node_place(graph, dimensions, up_es, down_es, settings)
    #TODO: NodeData
    node_info: Dict[str, Tuple[Coord, FixedMap]] = {node: (loc, fixed_cmaps.node_to_fixedmap(node, graph.nodes[node].data)) for node, loc in node_locs.items()}
    rnodes = list(graph.nodes.keys())
    random.shuffle(rnodes)
    # Holds all the paths, along with their constraints (TODO: the constraints)
    #TODO: can get unlucky with elevator placement of multiple elevators
    #   See output/error.png
    paths: List[Path] = []
    for node in rnodes:
        for edge in graph.nodes[node].edges:
            # Special case - edges from MB start from the escape point!
            if node == "Mother_Brain":
                start_point = node_locs[node] + Coord(-5, 0)
            else:
                start_point = node_locs[node]
            end_point = node_locs[edge.terminal]
            # path from n1 to n2
            # first, find all nodes reachable from n1 that are already placed
            _, o, f = cmap.map_bfs(start_point, None, reach_pred=cmap.step_on)
            # find the closest.
            dists = [(p, euclidean(p, node_locs[edge.terminal])) for p in list(f)]
            dists = sorted(dists, key=lambda n: n[1])
            #TODO: probability distribution over dists?
            closest, _ = dists[0]
            # Find the path to closest
            to_closest = get_path(o, start_point, closest)
            # Make a new path to that item from the closest reachable point
            offers, _ = cmap.map_search(closest, end_point,
                                        dist=dist, reach_pred=cmap.can_place)
            to_end = get_path(offers, closest, node_locs[edge.terminal])
            # Make the path into tiles
            #TODO: respect the constraints on the edge
            if to_end is not None:
                for xy in to_end:
                    if xy not in cmap:
                        cmap[xy] = MapTile()
            else:
                assert False, "Cannot find path: " + str(closest) + ", " + str(node_locs[edge.terminal])
            path = path_concat(to_closest, to_end)
            t = edge.terminal
            paths.append(Path(node, graph.nodes[node].data, t, graph.nodes[t].data, path, edge.data))
    # partition the map into random rooms
    room_size = len(cmap) // settings["room_size"]
    #_, rooms = cmap.random_rooms(room_size)
    rooms: Dict[Coord, Set[Coord]] = cmap.random_rooms_alt(room_size, bboxes)
    #TODO: Each room tries to grab the map tiles that are inside its bounding box!
    #TODO: Or could use a budgeted cellular automaton to fill in "corner" spaces with map tiles...
    #TODO: Phantoon's room winds up in rooms, as do elevators, etc...
    return cmap, rooms, paths, node_info

def random_node_place(graph, dimensions, up_es, down_es):
    """
    Returns a dictionary of node -> location by choosing locations for the nodes
    at random.
    """
    r = Rect(Coord(0, 0), dimensions)
    # Use as_list since set() is forbidden for ordering
    xys = r.as_list()
    locs = random.sample(xys, graph.nnodes)
    node_list = graph.nodes.keys()
    node_locs = {}
    # choose elevator locations: down elevators are the lowest locs, and up are the highest locs
    #TODO: seems like it doesn't always return the lowest n or highest n points
    sorted_locs = sorted(locs, key=lambda n: n.y)
    for node in node_list:
        if node in up_es:
            node_locs[node] = sorted_locs.pop(0) # highest y coordinate is further down
        elif node in down_es:
            node_locs[node] = sorted_locs.pop()
    node_list = [node for node in node_list if node not in up_es and node not in down_es]
    random.shuffle(node_list)
    #TODO: this is where we can make sure there is an item behind Draygon or some such??
    # -> pick an item node later in the order than Draygon and put it past Draygon?
    # -> default to supers
    for i in range(len(node_list)):
        if node_list[i] not in node_locs:
            node_locs[node_list[i]] = sorted_locs[i]
    return node_locs

def can_place(node_fmap, pos, cmap):
    """
    Area_maker is position -> cmap, bounding_box (optional)
    Intended for use with fixed_cmaps.mk_area() where area, and dims are known.
    True if the cmap generated by area_maker(pos) is valid, and can be composed with cmap.
    """
    node_cmap = node_fmap.cmap(pos, cmap.dimensions)
    if node_cmap is not None and cmap.compose(node_cmap, collision_policy="none", offset=pos) is not None:
            return True
    return False

def find_placement(initial, cmap, graph):
    """
    Find a placement of the nodes that allows their concrete maps to co-exist within
    the boundaries of cmap.
    Initial is a node_locs: node : location. cmap is a ConcreteMap.
    """
    final_node_locs = {}
    bboxes = []
    for node, init_pos in initial.items():
        node_fmap = fixed_cmaps.node_to_fixedmap(node, graph.nodes[node].data)
        g, _, _ = cmap.map_bfs(init_pos, lambda p: can_place(node_fmap, p, cmap))
        assert g is not None, "No valid place found."
        final_node_locs[node] = g
        # Actually place it into the map
        i_cmap = node_fmap.cmap(g, cmap.dimensions)
        i_bboxes = [bbox.translate(g) for bbox in node_fmap.bboxes]
        cmap = cmap.compose(i_cmap, offset=g)
        bboxes.extend(i_bboxes)
    return final_node_locs, cmap, bboxes

def node_place(graph, dimensions, up_es, down_es, settings):
    """
    Find a placement for nodes where their respective areas do not violate
    each other.
        Random initially, with elevators guaranteed to be at the top and bottom (initially)
        Subjected to a spring model which reduces the total potential energy (moves far nodes closer)
        Subject to a search so that nodes can be placed without violating each other's areas.
    """
    initial = random_node_place(graph, dimensions, up_es, down_es)
    spring = spring_model(initial, graph, 
                          settings["n_iterations"],
                          settings["spring_constant"],
                          settings["equilibrium"],
                          settings["spring_dt"],
                          settings["spring_damping"])
    trunc_spring = {n : xy.truncate(Coord(0, 0), dimensions) for (n, xy) in spring.items()}
    # Now do a search for a good placement for each nod.
    cmap = ConcreteMap(dimensions)
    return find_placement(trunc_spring, cmap, graph)

#TODO
def connecting_path(cmap, t1, t2, threshold):
    """creates a path from t1 to t2 if
    bfs_d(t1, t2) / d(t1, t2) exceeds threshold."""
    assert t1 in cmap, str(t1) + " not in cmap."
    assert t2 in cmap, str(t1) + " not in cmap."
    assert not cmap[t1].is_fixed
    assert not cmap[t2].is_fixed
    _, o, f = cmap.map_bfs(t1, lambda x: x == t2, reach_pred=lambda x: x in cmap and not cmap[x].is_fixed)
    p = get_path(o, t1, t2)
    ratio = len(p) / (euclidean(t1, t2) + 1e-5) # epsilon for nonzero
