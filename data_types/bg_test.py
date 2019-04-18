from basicgraph import *

if __name__ == "__main__":
    g = BasicGraph()
    g.add_node("ayy")
    g.add_node("lmao")
    g.add_edge("ayy", "lmao")
    g.add_edge("lmao", "ayy")
    g.visualize("ayylmao")

