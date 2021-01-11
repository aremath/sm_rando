from sm_rando.encoding.parse_rooms import *
from sm_rando.data_types.constraintgraph import *
from sm_rando.data_types.orderedset import OrderedSet

def test_network_flow():
    # Build a graph
    g = ConstraintGraph()
    g.add_node("source")
    g.add_node("sink")
    edge_weights = {}
    nodes = ["{}_{}".format(i+1, k) for i in range(10) for k in range(2)]
    for node in nodes:
        g.add_node(node)
    for i in range(10):
        n0 = "{}_{}".format(i+1, 0)
        n1 = "{}_{}".format(i+1, 1)
        g.add_edge(n0, n1)
        edge_weights[(n0, n1)] = 1
        edge_weights[(n1, n0)] = 0
    edges = [
        ("source", "1_0"),
        ("source", "2_0"),
        ("1_1", "3_0"),
        ("2_1", "4_0"),
        ("2_1", "5_0"),
        ("3_1", "6_0"),
        ("3_1", "7_0"),
        ("4_1", "8_0"),
        ("5_1", "8_0"),
        ("6_1", "sink"),
        ("7_1", "sink"),
        ("8_1", "9_0"),
        ("8_1", "10_0"),
        ("9_1", "10_0"),
        ("10_1", "sink")
        ]
    for e1, e2 in edges:
        g.add_edge(e1, e2)
        edge_weights[(e1, e2)] = 2
        edge_weights[(e2, e1)] = 0
    # Now do network flow:
    return (g.network_flow(edge_weights, "source", "sink"))

def test_bfs_items():
    rooms = parse_rooms("encoding/dsl/rooms.txt")
    #finished, completed, complete_items = rooms["Ice_Beam"][0].graph.BFS_items("Ice_Beam_L")
    start_state = BFSItemsState("Frog_Speedway_R", wildcards_=OrderedSet(["Item_Dummy"]))
    offers, finished,  _, _ = rooms["Frog_Speedway"].graph.BFS_items(start_state)
    print("finished")
    print(finished)

if __name__ == "__main__":
    print(test_network_flow())
