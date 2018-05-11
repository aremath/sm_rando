import itertools

class BasicGraph(object):

    def __init__(self):
        self.nodes = {} # key - node name, value - node data
        self.nnodes = 0

    def add_node(self, name, data=None):
        if name is None:
                name = str(self.nodes)
        assert name not in self.nodes, "A node with this name already exists: " + name
        self.nnodes += 1
        self.nodes[name] = Node(data)
        pass

    def add_edge(self, node1, node2, data=None):
        assert node1 in self.nodes, "Node does not exist: " + node1
        assert node2 in self.nodes, "Node does not exist: " + node2
        # check if there already is an edge:
        for edge in self.nodes[node1].edges:
            assert edge.terminal != node2, "An edge already exists: " + node1 + " -> " + node2
        edge = Edge(node2, data)
        self.nodes[node1].edges.append(edge)

    def update_edge(self, node1, node2, data=None):
        """new data for the edge between n1 and n2"""
        if self.is_edge(node1, node2):
            #TODO innefficient!
            for edge in self.nodes[node1].edges:
                if edge.terminal == node2:
                    edge.data = data
        else:
            self.add_edge(node1, node2, data)

    def update_edge_append(self, node1, node2, data):
        """append data to the edge between n1 and n2"""
        if self.is_edge(node1, node2):
            #TODO innefficient!
            for edge in self.nodes[node1].edges:
                if edge.terminal == node2:
                    edge.data.append(data)
        else:
            self.add_edge(node1, node2, data)

    def is_edge(self, node1, node2, p=lambda x: True):
        """ is there an edge from node1 to node2 satisfying p?"""
        assert node1 in self.nodes, "Node does not exist: " + node1
        assert node2 in self.nodes, "Node does not exist: " + node2
        for edge in self.nodes[node1].edges:
            if edge.terminal == node2 and p(edge.data):
                return True
        return False

    def get_edge_data(self, node1, node2):
        """ get the data (if any), in the edge from n1 to n2 """
        assert node1 in self.nodes, "Node does not exist: " + node1
        assert node2 in self.nodes, "Node does not exist: " + node2
        for edge in self.nodes[node1].edges:
            if edge.terminal == node2 and p(edge.data):
                return edge.data
        return None

    def remove_edge(self, node1, node2):
        assert node1 in self.nodes, "Node does not exist: " + node1
        assert node2 in self.nodes, "Node does not exist: " + node2
        for index, edge in enumerate(self.nodes[node1].edges):
            if edge.terminal == node2:
                del self.nodes[node1].edges[index]
                return
        assert False, "No such edge: " + node1 + " -> " + node2

    def remove_node(self, node):
        assert node in self.nodes, "Node does not exist: " + node
        self.nnodes -= 1
        del self.nodes[node]
        for inode in self.nodes:
            indices_to_delete = []
            for index, edge in enumerate(inode.edges):
                if edge.terminal == node:
                    indices_to_delete.append(index)
            for index in indices_to_delete:
                del node.edges[index]

    def subgraph(self, nodes):
        """Returns a new graph which is a subgraph of self, using the nodes of nodes.
           Data will typically be shared by nodes and edges."""
        sgraph = BasicGraph()
        # add the nodes
        for node in nodes:
            sgraph.add_node(node, self.nodes[node].data)
        # make the edges
        for n1, n2 in itertools.permutations(nodes, r=2):
            if self.is_edge(n1, n2):
                sgraph.add_edge(n1, n2)
        return sgraph

    #TODO: add a predicate to test the node data or the edge data for impassibility
    def BFS(self, start, end=None):
        # key - node name
        # value - the previous node in the BFS
        offers = {}
        finished = set()
        queue = [start]
        node = ""
        while len(queue) > 0:
            node = queue.pop()
            if end is not None and node == end:
                break
            finished |= set([node])
            for neighbor in self.nodes[node].edges:
                if neighbor.terminal not in finished:
                    queue.append(neighbor.terminal)
                    offers[neighbor.terminal] = node
        return finished, offers

    def copy(self):
        """Returns a copy of self - pointers to data might still be entangled."""
        new_graph = BasicGraph()
        for node_name, node in self.nodes.items():
            new_graph.add_node(node_name, node.data)
        for node_name, node in self.nodes.items():
            for edge in node.edges:
                new_graph.add_edge(node_name, edge.terminal, edge.data)
        return new_graph

    def get_edges(self):
        """returns all the edges in self as a list of node tuples"""
        #TODO: generator?
        edges = []
        for node_name, node in self.nodes.items():
            for edge in node.edges:
                edges.append((node_name, edge.terminal))
        return edges

    def __repr__(self):
        self_str = ""
        for node_name, node in self.nodes.iteritems():
            self_str += node_name
            if node.data is not None:
                self_str += "\t" + str(node.data)
            self_str += "\n"
            for edge in node.edges:
                self_str += "\t" + str(edge.terminal)
                if edge.data is not None:
                    self_str += "\t" + str(edge.data)
                self_str += "\n"
        # remove trailing \n
        return self_str[-1]

    def visualize(self, fname):
        """Use graphviz to show the graph, as <fname>.pdf"""
        import graphviz
        dot = graphviz.Digraph()
        # put in the nodes
        for node_name in self.nodes:
            dot.node(node_name, node_name)
        # put in the edges
        for node_name in self.nodes:
            for edge in self.nodes[node_name].edges:
                dot.edge(node_name, edge.terminal) #TODO: label as the string of edge.data?
        dot.render(fname)

class Node(object):
    
    def __init__(self, data=None):
        self.edges = []
        self.data = data

class Edge(object):
    
    def __init__(self, terminal, data=None):
        self.terminal = terminal
        self.data = data

# find the path from start to end given a bfs_offers
def bfs_path(offer, start, end):
    path = []
    node = end
    if end not in offer:
        return None
    else:
        while node != start:
            path.append(node)
            node = offer[node]
        # reverse the path
        return path[:-1]
