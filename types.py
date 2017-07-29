class ConstraintGraph:
	'''A graph where the nodes are doors or items, and
	the edges encode reachability constraints'''

	def __init__(self, level_name):
		self.level_name = level_name
		# key - node
		# value - edge list for that node
		self.node_dict = {}
		self.nnodes = 0

	def add_node(self, node_name, node_data):
		node = ConstraintNode(self, node_name, node_data)
		self.node_dict[node] = []
		self.nnodes += 1
		return node

	def add_directed_edge(self, node1, node2, items=MinSetSet()):
		# check if there is already an edge from 1 to 2.
		# if there is, then AND their minsets together
		for edge in self.node_dict[node1]:
			if edge.terminal == node2:
				edge.items *= items
				return
		edge = ConstraintEdge(items, node2)
		self.node_dict[node1].append(edge)

	def add_undirected_edge(self, node1, node2, items=MinSetSet()):
		self.add_directed_edge(node1, node2, items)
		self.add_directed_edge(node2, node1, items)

	def BFS(self, node1, node2, items=set()):
		'''Returns a path from node1 to node2 - none if there is no path.
		Also returns a function which is the union of the constraint functions
		along that path.'''
		path = []
		pass

	def reachable(self, node, items=set()):
		'''Returns a list of nodes which are reachable from node'''
		pass

	def all_paths(self, node1, node2, items=set()):
		'''Returns all paths (as node lists) from node1 to node2'''
		# NOTE - restrict based on size - there are often an infinite number of
		# paths from s to t. The room graphs are likely to be close to connected.
		# maybe just ensure that no node can appear in any path twice?
		pass

	def add_subgraph(self, graph):
		'''Adds the nodes from graph as a subgraph in graph. Makes copies of the node and edge data
		rather than using the same nodes. Returns a list of the added nodes.'''
		# key - old node
		# value - new node
		copy_nodes = {}
		for node in graph.node_dict.keys():
			new_node = self.add_node(node.name, node.data):
			copy_nodes[node] = new_node
		for node, edges in graph.node_dict.iteritems():
			for edge in edges:
				self.add_directed_edge(copy_nodes[node], copy_nodes[edge.terminal], edge.items)
		return copy_nodes.values()

	def edges_to(self, node_to, search=None, items=set()):
		'''Given a list of nodes to search, return a list of nodes with edges to node_to that the
		given item set matches the constraints for. Defaults to searching the entire graph.'''
		if search is None:
			search = self.node_dict.keys()
		node_list = []
		for node in search:
			include = False
			for edge in node_dict[node]:
				if edge.terminal == node_to and edge.items.matches(items):
					include = True
			if include:
				node_list.append(node)
		return node_list

	def prune_graph(self, items):
		'''Returns a new graph with the same node data, but without edges that the item set doesn't pass.
		Removes nodes with no edges.'''
		# TODO: this doesn't quite work...
		new_graph = ConstraintGraph(self.level_name)
		for node, edges in self.node_dict.iteritems():
			new_node = ConstraintNode(node.data)
			for edge in edges:
				if edge.items.matches(items):
					new_edge = ConstraintEdge(edge.items, edge.terminal)
		#

class ConstraintEdge:

	def __init__(self, items=MinSetSet(), terminal):
		self.items = items
		self.terminal = terminal


class ConstraintNode:

	def __init__(self, name, data):
		self.name = name
		self.data = data

class Door:

	def __init__(self, name, address, items=MinSetSet(), accessible=True):
		self.name = name
		self.mem_address = address
		self.items = items
		self.accessible = accessible

class Item:

	def __init__(self, name, address, item_type = ""):
		self.name = name
		self.mem_address = address
		self.type = item_type

class Room:

	def __init__(self, address, room_defn):
		self.mem_address = address
		self.name = ""
		# parse the room_defn to get the room name, and create
		# a ConstraintGraph that encodes the room.

		# also create a node dict - key = node name, value = node
		# also create a doors dict - key = direction (L R B T ET EB TS BS LMB RMB), value = door names for that direction


def doors_in(doors, door_expr):
	'''Takes an expression of doors, and returns
	a list of door names that satisfy that expression.'''
	#(D1 D2 ... DN)
	#ALL
	#D1
	pass

def ConnectedGraph(nodes):
	"""connects the specified nodes"""
	# node_constraints is a dict with key - node name, value - MinSetSet required to pass that node.
	graph = ConstraintGraph(room_name)
	for node in node_names:
		node = ConstraintNode()

