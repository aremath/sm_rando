from data_types import basicgraph
from encoding import item_order
import random
import heapq
import collections
import itertools

def order_graph():
    """Creates an item order graph, which is an
        order in which the items may be picked up
        and a set of tentative paths to do that"""
    g = basicgraph.BasicGraph()
    order = item_order.order()
    g.add_node("START")
    current = "START"
    things = set()
    for index, i in enumerate(order):
        # first, BFS from current to find a candidate entrance
        finished, offers = g.BFS(current)

        # choose the entrance at random
        entrance = random.choice(list(finished))
        #TODO: update the paths from current to finished with the path info (which things we have)
        #path = basicgraph.bfs_path(offers, current, entrance
        # choose the exit at random
        exit = random.choice(g.nodes.keys())

        # add the new node
        iname = i
        g.add_node(iname)
        g.add_edge(entrance, iname)
        g.add_edge(iname, exit)
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
    #TODO: does this work, or do I need to use heappush?
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
    n_elevators = 0
    crossings = find_crossings(graph, regions)
    for regs, edges in crossings.items():
        r1, r2 = tuple(regs)
        assert (len(edges) > 0), "Invalid regions: no nodes in " + r1 + ", " + r2
        n_elevators += 1
        # n1 has an edge to n2 crossing either from r1->r2 or r2->r1
        r1_e_name = "Elevator " + r1 + "+" + r2 + " @ " + r1
        r2_e_name = "Elevator " + r1 + "+" + r2 + " @ " + r2
        graph.add_node(r1_e_name)
        graph.add_node(r2_e_name)
        regions[r1].add(r1_e_name)
        regions[r2].add(r2_e_name)
        graph.add_edge(r1_e_name, r2_e_name)
        graph.add_edge(r2_e_name, r1_e_name)
        for n1, n2 in edges:
            if n1 in regions[r1]:
                graph.update_edge(n1, r1_e_name)
                #TODO: update the r1_e -> r2_e edge
                graph.update_edge(r2_e_name, n2) 
            elif n1 in regions[r2]:
                graph.update_edge(n1, r2_e_name)
                graph.update_edge(r1_e_name, n2)
            else:
                assert False, "Node not in either region: " + n1
    return n_elevators
        

# crossings:
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
                        crossings[fset].append((node1, node2))
    return crossings

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
