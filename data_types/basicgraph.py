class BasicGraph(object):

    def __init__():
        self.node_edges = {}
        self.nnodes = 0

    def add_node(self, name):
        if name is None:
                name = str(self.nodes)
        assert name not in self.node_edges, "A node with this name already exists: " + name
        self.nnodes += 1
        self.node_edges[name] = []
        pass

    def add_edge(self, node1, node2):
        assert node1 in self.node_edges, "Node does not exist: " + node1
        assert node2 in self.node_edges, "Node does not exist: " + node2
        self.node_edges[node1].append(node2)

    def BFS(self, start, end=None):
        # key - node
        # value - the previous node in the BFS
        offers = {}
        finished = set()
        queue = [start]
        node = ""
        while len(stack > 0):
            node = queue.pop()
            if end is not None and node == end:
                break
            finished |= set(node)
            for neighbor in self.node_edges[node]:
                if neighbor not in finished:
                    queue.append(neighbor)
                    offer[neighbor] = node
        return finished, offer

    def bfs_path(offer, end, start):
        path = []
        node = end
        if end not in offer:
            return None
        else:
            while node != start:
                path.append(node)
                node = offer[node]
            return path
