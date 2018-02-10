from world_rando import item_order_graph

if __name__ == "__main__":
    o, g = item_order_graph.order_graph()
    g.visualize("order")
    print o
