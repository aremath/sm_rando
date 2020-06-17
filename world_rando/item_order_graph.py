import random
import heapq
import collections
import itertools

from sm_rando.data_types import basicgraph, item_set
from sm_rando.encoding import item_order, sm_global

#TODO: every item needs to keep a unique ID
# so that it can know its PLM index when it
# comes time to place it as a PLM.
# Can do this later when determining PLM placement, keeping a counter of items placed

def abstract_map(settings):
    """puts it all together to make an abstract map with regions and elevators"""
    order, graph = order_graph()
    #TODO: add items before or after partition?
    # after is probably better...
    add_items(graph, settings["extra_items"])
    #region_order, region_finished = partition_order(graph, sm_global.regions)
    region_order, region_finished = weighted_partition_order(graph, sm_global.regions, settings["region_weights"])
    elevators = make_elevators(graph, region_finished)
    region_order = item_order.region_order()
    es = elevator_directions(elevators, region_order)
    rsg = region_subgraphs(graph, region_finished)
    return order, graph, rsg, es, region_order

#TODO: item annotations
def order_graph():
    """Creates an item order graph, which is an
        order in which the items may be picked up
        and a set of tentative paths to do that"""
    g = basicgraph.BasicGraph()
    order = item_order.order()
    g.add_node("START")
    current = "START"
    things = item_set.ItemSet()
    for index, i in enumerate(order):
        # first, BFS from current to find a candidate entrance
        finished, offers = g.BFS(current)

        # choose the entrance at random
        entrance = random.choice(list(finished))
        path = basicgraph.bfs_path(offers, current, entrance)
        # add things constraints along the path
        #for i in range(len(path)):
        #    if i + 1 < len(path):
        #        g.update_edge_append(path[i], path[i+1], things.copy())

        # choose the exit at random
        exit = random.choice(list(g.nodes.keys()))

        # add the new node
        iname = i
        g.add_node(iname)
        g.add_edge(entrance, iname, data=[things.copy()])
        things.add(iname)
        g.add_edge(iname, exit, data=[things.copy()])
    return order, g

def partition_order(graph, initial, priority=lambda x: 0):
    """Partitions the item order graph into regions."""
    # initial is a dictionary with
    # key - region name (ex. "Maridia")
    # value - nodes in that region

    gnodes = set(graph.nodes.keys())
    # key - region name, value - offers for that region
    roffers = { region: {} for region in initial}
    # key - region name, value - finished for that region
    rfinished = {region: set() for region in initial}
    for region in initial:
        for node in initial[region]:
            rfinished[region].add(node)
    # key - region name, value, list of places in that region
    rheaps = {region: [(priority(i), i) for i in initial[region]] for region in initial}

    # build all_finished
    all_finished = set()
    for rnodes in initial.values():
        all_finished |= set(rnodes)

    while all_finished != gnodes:
        for region in initial.keys():
            #TODO: maybe something smarter than this special-case
            if region == "Tourian":
                continue
            if len(rheaps[region]) > 0:
                _, rnode = heapq.heappop(rheaps[region])
            else:
                continue
            for e in graph.nodes[rnode].edges:
                t = e.terminal
                if t not in all_finished:
                    heapq.heappush(rheaps[region], (priority(t), t))
                    rfinished[region].add(t)
                    roffers[region][t] = rnode
                    all_finished.add(t)

    return roffers, rfinished

# given a set of regions, make the necessary elevators
# need to:
#   1. Find edges that cross region boundaries
#   2. Make an elevator for each unique region crossing
#
def make_elevators(graph, regions):
    elevators = collections.defaultdict(list)
    crossings = find_crossings(graph, regions)
    for regs, edges in crossings.items():
        r1, r2 = tuple(regs)
        assert (len(edges) > 0), "Invalid regions: no nodes in " + r1 + ", " + r2
        # n1 has an edge to n2 crossing either from r1->r2 or r2->r1
        r1_e_name = "Elevator " + r1 + "+" + r2 + " @ " + r1
        r2_e_name = "Elevator " + r1 + "+" + r2 + " @ " + r2
        elevators[r1].append((r1_e_name, r2))
        elevators[r2].append((r2_e_name, r1))
        graph.add_node(r1_e_name)
        graph.add_node(r2_e_name)
        regions[r1].add(r1_e_name)
        regions[r2].add(r2_e_name)
        graph.add_edge(r1_e_name, r2_e_name)
        graph.add_edge(r2_e_name, r1_e_name)
        for n1, n2, d in edges:
            if n1 in regions[r1]:
                graph.update_edge(n1, r1_e_name, d)
                graph.update_edge(r2_e_name, n2, d) 
                #graph.update_edge_append(r1_e_name, r2_e_name, d)
            elif n1 in regions[r2]:
                graph.update_edge(n1, r2_e_name, d)
                graph.update_edge(r1_e_name, n2, d)
                #graph.update_edge_append(r2_e_name, r1_e_name, d)
            else:
                assert False, "Node not in either region: " + n1
    return elevators
        

# Find the places where the edges of a graph cross a given partitioning of it.
# Crossings:
# key1 - set of region1, region2
# value - list of node1, node2 pairs
# such that n1 is in r1, n2 is in r2, and n1 has an edge to n2
def find_crossings(graph, regions):
    crossings = collections.defaultdict(list)
    for region1, region2 in itertools.permutations(regions, r=2):
        fset = frozenset([region1, region2])
        for node1 in regions[region1]:
            for node2 in regions[region2]:
                for e in graph.nodes[node1].edges:
                    if e.terminal == node2:
                        crossings[fset].append((node1, node2, e.data))
    return crossings

#TODO: Why do we need this?
# Find what region a node is in.
def node_in_region(node, regions):
    for region in regions:
        if node in regions[region]:
            return region
    assert False, "Node not in regions"

def region_subgraphs(graph, regions):
    region_sgraphs = {}
    for region, nodes in regions.items():
        region_sgraphs[region] = graph.subgraph(nodes)
    return region_sgraphs

def elevator_directions(elevators, region_order):
    up_es = set()
    down_es = set()

    for r1, t_list in elevators.items():
        for t in t_list:
            e_name, r2 = t
            # determine if r1 is before or after r2
            r1_index = region_order.index(r1)
            r2_index = region_order.index(r2)
            if r1_index > r2_index:
                down_es.add(e_name)
            elif r2_index > r1_index:
                up_es.add(e_name)
            else:
                assert False, "Elevator to same region"
    return up_es, down_es

def add_items(graph, items):
    """adds the requested amount of each item to the specified abstract map
    randomly. Items is a dictionary with key - item type to add, value - number to add"""
    for item_type, n in items.items():
        assert item_type in sm_global.items, item_type + " is not a valid item!"
        for i in range(n):
            #TODO: where to connect to it?
            #   - need to be able to know what items we have at the location
            #   - at this point, only edges know this info...?
            # for now, pick a random edge and intersperse the node on it
            node_name = item_type + str(i)
            from_node = random.choice(list(graph.nodes.keys()))
            graph.add_node(node_name)
            graph.add_edge(from_node, node_name)
            graph.add_edge(node_name, from_node)
            #TODO: need to store item information on each of these edges?
            #TODO: store what type of item it is in the node data?

def make_rand_weighted_list(weights):
    """Create a shuffled list using weights. Weights is a key->int dict that contains how 
    many of each key to place into the weighted list."""
    out = []
    for key, weight in weights.items():
        out.extend([key]*weight)
    random.shuffle(out)
    return out

#TODO: a way to make this have less variance?
#   A parameter that determines how often every region gets a choice versus
#   pulling from the weighted list.
def weighted_partition_order(graph, initial, weights, priority=lambda x: 0):
    """Partitions the item order graph into regions."""
    # initial: region name (ex. "Maridia") -> nodes in that region
    # weights: region name -> total weight for that region (int)
    # The weights are not normalized, but for example if the weight sums to 100,
    # and the weight of "Tourian" is 2, then the Tourian region should have 2 chances
    # to grab a node for every 100 total chances. Note that this changes as the set of
    # live regions changes. A region with no unclaimed neighbors has no chances to grab
    # any nodes.

    gnodes = set(graph.nodes.keys())
    # roffers: region name -> offers for that region (node set)
    roffers = { region: {} for region in initial}
    # rfinished: region name -> finished for that region (node set)
    rfinished = {region: set() for region in initial}
    # Initialize rfinished with initial
    for region in initial:
        for node in initial[region]:
            rfinished[region].add(node)
    # rheaps: region name -> list of nodes in that region (with priority)
    rheaps = {region: [(priority(i), i) for i in initial[region]] for region in initial}

    # all_finished is the set of nodes that have a region assignment
    all_finished = set()
    for rnodes in initial.values():
        all_finished |= set(rnodes)

    # Determines which region's turn it is
    node_chances = []

    # stop when every node has a region assignment
    while all_finished != gnodes:
        # If we've gone through the list of chances, re-generate it
        if len(node_chances) == 0:
            node_chances = make_rand_weighted_list(weights)
        # choose the current region from node_chances
        region = node_chances.pop()
        # If there are nodes with live neighbors...
        if len(rheaps[region]) > 0:
            _, rnode = heapq.heappop(rheaps[region])
        # If there are no nodes with live neighbors, remove this node from the list of chances
        # and remove it from the weights dictionary. This region is no longer live.
        else:
            del weights[region]
            node_chances = [r for r in node_chances if r != region]
            continue
        # Add the node's neighbors
        #TODO: only add one of its neighbors at a time?
        for e in graph.nodes[rnode].edges:
            t = e.terminal
            if t not in all_finished:
                heapq.heappush(rheaps[region], (priority(t), t))
                rfinished[region].add(t)
                roffers[region][t] = rnode
                all_finished.add(t)

    return roffers, rfinished

