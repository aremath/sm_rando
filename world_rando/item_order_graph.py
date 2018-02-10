from data_types import basicgraph
from encoding import item_order
import random

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
        iname = i + "_" + str(index)
        g.add_node(iname)
        g.add_edge(entrance, iname)
        g.add_edge(iname, exit)
    return order, g

