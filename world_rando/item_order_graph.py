import random
import heapq
import collections
import itertools
import operator
from enum import IntEnum

from data_types import basicgraph, item_set
from encoding import item_order
from world_rando.util import pairwise

#TODO: every item and door cap needs to keep a unique ID
# so that it can know its PLM index when it
# comes time to place it as a PLM.
# Can do this later when determining PLM placement, keeping a counter of items placed

# What type is each node?
class NodeType(IntEnum):
    SAVE = 0
    ITEM = 1
    BOSS = 2
    SHIP = 3
    ELEVATOR_UP = 4
    ELEVATOR_DOWN = 5

def abstract_map(settings, gsettings):
    """puts it all together to make an abstract map with regions and elevators"""
    order = item_order.order(settings["required_nodes"], settings["node_ordering"])
    print(order)
    graph = order_graph(order)
    #TODO: add items before or after partition?
    # after is probably better...
    add_nodes(graph, settings["extra_nodes"])
    #_, region_finished = partition_order(graph, sm_global.regions)
    # Filter the initial conditions by nodes that are actually present
    initial = {r: list(filter(lambda x: x in graph, r.required_nodes)) for r in gsettings["regions"]}
    weights =  {r: r.partition_weight for r in gsettings["regions"]}
    _, region_finished = weighted_partition_order(graph, initial, weights)
    # Get the set of regions to generate from settings
    # Need to use the actual string names or the ordering will not work...
    region_names = {r.name: r for r in gsettings["regions"]}
    region_order = item_order.region_order(list(region_names.keys()), settings["region_ordering"])
    region_order = [region_names[r] for r in region_order]
    elevators = make_elevators(graph, region_finished, region_order)
    #es = elevator_directions(elevators, region_order)
    rsg = region_subgraphs(graph, region_finished)
    #print(es)
    return order, graph, rsg, region_order

def order_graph(order):
    """Creates an item order graph, which is an
        order in which the items may be picked up
        and a set of tentative paths to do that"""
    #TODO: convert to networkx
    g = basicgraph.BasicGraph()
    g.add_node("START", NodeType.SHIP)
    current = "START"
    current_items = item_set.ItemSet()
    for item_name in order:
        # first, BFS from current to find a candidate entrance
        finished, offers = g.BFS(current)

        # Choose the entrance at random
        entrance = random.choice(list(finished))
        path = basicgraph.bfs_path(offers, current, entrance)
        # Add items along the path
        for a, b in pairwise(path):
            g.update_edge_lambda(a, b, [current_items.copy()], operator.add)

        # Choose the exit at random from among the existing nodes
        exit = random.choice(list(g.nodes.keys()))

        # Add the new node
        #TODO: this doesn't necessarily use the appropriate nodetype
        #TODO: this doesn't update the current node!
        g.add_node(item_name, NodeType.ITEM)
        g.add_edge(entrance, item_name, data=[current_items.copy()])
        current_items = current_items.add(item_name)
        g.add_edge(item_name, exit, data=[current_items.copy()])
    return g

def partition_order(graph, initial, priority=lambda x: 0):
    """Partitions the item order graph into regions."""
    # initial is a dictionary with
    # Key - region name (ex. "Maridia")
    # Value - nodes in that region

    gnodes = set(graph.nodes.keys())
    # key - region name, value - offers for that region
    roffers = {region: {} for region in initial}
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

def elevator_directions(r1, r2, region_order):
    # Return the directions of r1 -> r2 and r2 -> r1 respectively
    # Determine if r1 is before or after r2
    r1_index = region_order.index(r1)
    r2_index = region_order.index(r2)
    # Earlier in the order list means lower down
    if r1_index > r2_index:
        return NodeType.ELEVATOR_DOWN, NodeType.ELEVATOR_UP
    elif r2_index > r1_index:
        return NodeType.ELEVATOR_UP, NodeType.ELEVATOR_DOWN
        up_es.add(e_name)
    else:
        assert False, "Elevator to same region"

def make_elevators(graph, regions, region_order):
    """
    Given a set of regions, make the necessary elevators
    Need to:
        1. Find edges that cross region boundaries
        2. Make an elevator for each unique region crossing
    """
    elevators = collections.defaultdict(list)
    crossings = find_crossings(graph, regions)
    for regs, edges in crossings.items():
        r1, r2 = tuple(regs)
        e1_direction, e2_direction = elevator_directions(r1, r2, region_order)
        assert (len(edges) > 0), f"Invalid regions: no nodes in {r1}, {r2}"
        # n1 has an edge to n2 crossing either from r1->r2 or r2->r1
        r1_e_name = f"Elevator {r1.name} + {r2.name} @ {r1.name}"
        r2_e_name = f"Elevator {r1.name} + {r2.name} @ {r2.name}"
        elevators[r1].append((r1_e_name, r2))
        elevators[r2].append((r2_e_name, r1))
        graph.add_node(r1_e_name, e1_direction)
        graph.add_node(r2_e_name, e2_direction)
        regions[r1][r1_e_name] = None
        regions[r2][r2_e_name] = None
        graph.add_edge(r1_e_name, r2_e_name, [])
        graph.add_edge(r2_e_name, r1_e_name, [])
        for n1, n2, d in edges:
            # Add the necessary edges
            if n1 in regions[r1]:
                graph.update_edge_lambda(n1, r1_e_name, d, operator.add)
                graph.update_edge_lambda(r1_e_name, r2_e_name, d, operator.add)
                graph.update_edge_lambda(r2_e_name, n2, d, operator.add)
            elif n1 in regions[r2]:
                graph.update_edge_lambda(n1, r2_e_name, d, operator.add)
                graph.update_edge_lambda(r2_e_name, r1_e_name, d, operator.add)
                graph.update_edge_lambda(r1_e_name, n2, d, operator.add)
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
        pair_key = tuple(sorted([region1, region2]))
        for node1 in regions[region1]:
            for node2 in regions[region2]:
                for e in graph.nodes[node1].edges:
                    if e.terminal == node2:
                        crossings[pair_key].append((node1, node2, e.data))
    return crossings

#TODO: Why do we need this?
def node_in_region(node, regions):
    """
    Find what region a node is in
    """
    for region in regions:
        if node in regions[region]:
            return region
    assert False, "Node not in regions"
    return None

def region_subgraphs(graph, regions):
    """
    Create a subgraph for each region
    """
    region_sgraphs = {} 
    for region, nodes in regions.items():
        region_sgraphs[region] = graph.subgraph(nodes)
    return region_sgraphs

def add_nodes(graph, extra_items):
    """adds the requested amount of each item to the specified abstract map
    randomly. Items is a dictionary with key - item type to add, value - number to add"""
    for item_type, n in extra_items.items():
        for i in range(n):
            #TODO: at some point, can have a from_node and a to_node that this item is between
            node_name = item_type + str(i)
            from_node = random.choice(list(graph.nodes.keys()))
            #TODO: choose this more wisely
            # Choose a random feasible item set
            # Choose an item set used on an edge that you use to leave from_node
            #TODO: for all assumed items, I think we'd like to ensure (if possible) that the player has that item as well
            out_edge = random.choice(graph.nodes[from_node].edges)
            assumed_items = random.choice(out_edge.data)
            if item_type == "Save":
                ty = NodeType.SAVE
            else:
                ty = NodeType.ITEM
            graph.add_node(node_name, ty)
            graph.add_edge(from_node, node_name, [assumed_items])
            graph.add_edge(node_name, from_node, [assumed_items])

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
#TODO: Determine initial ahead of time by filtering out nodes that are not required.
#   This would allow the re-use of a single "initial" across multiple settings,
#   Even when those settings require the placement of different items.
def weighted_partition_order(graph, initial, weights, priority=lambda x: 0):
    """Partitions the item order graph into regions."""
    # initial: region (ex. Maridia) -> nodes in that region
    # weights: region name -> total weight for that region (int)
    # The weights are not normalized, but for example if the weight sums to 100,
    # and the weight of "Tourian" is 2, then the Tourian region should have 2 chances
    # to grab a node for every 100 total chances. Note that this changes as the set of
    # live regions changes. A region with no unclaimed neighbors has no chances to grab
    # any nodes.
    # This process uses weights destructively
    weights = weights.copy()

    # set() is ok: order never used
    gnodes = set(graph.nodes.keys())
    # roffers: region name -> offers for that region (node set)
    roffers = {region: {} for region in initial}
    # rfinished: region name -> finished for that region (node set)
    # Use {} instead of set for stable ordering purposes
    rfinished = {region: {} for region in initial}
    # Initialize rfinished with initial
    for region in initial:
        for node in initial[region]:
            rfinished[region][node] = None
    # rheaps: region name -> list of nodes in that region (with priority)
    rheaps = {region: [(priority(i), i) for i in initial[region]] for region in initial}

    # all_finished is the set of nodes that have a region assignment
    # set() is ok: order is never used
    all_finished = set()
    for rnodes in initial.values():
        all_finished |= set(rnodes)

    # Determines which region's turn it is
    node_chances = []

    # Stop when every node has a region assignment
    while all_finished != gnodes:
        # If we've gone through the list of chances, re-generate it
        if len(node_chances) == 0:
            node_chances = make_rand_weighted_list(weights)
        # Choose the current region from node_chances
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
                rfinished[region][t] = None
                roffers[region][t] = rnode
                all_finished.add(t)
    return roffers, rfinished
