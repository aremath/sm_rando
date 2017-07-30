# all classes for implementing ConstraintGraph

from minsetset import *

class ConstraintGraph:

	def __init__(self):
		self.name_node = {}
		self.node_edges = {}
		self.nnodes = 0

	def add_node(self, name=None, node_data=None):
		# name is the ID value - need something to hash the node by.
		if name is None:
			name = str(self.nnodes)
		node = ConstraintNode(name, node_data)
		# make sure the name is unique
		assert name not in self.name_node, "A node with this name already exists: " + name
		self.name_node[name] = node
		self.node_edges[name] = []
		self.nnodes += 1
		return name

	def add_edge(self, node1, node2, items=MinSetSet()):
		assert node1 in self.name_node, "Node does not exist: " + node1
		assert node2 in self.name_node, "Node does not exist: " + node2
		# check if an edge already exists: if it does, and their sets
		for edge in self.node_edges[node1]:
			if edge.terminal == node2:
				edge.items *= items
				return
		edge = ConstraintEdge(items, node2)
		self.node_edges[node1].append(edge)

	def add_undirected_edge(self, node1, node2, items=MinSetSet()):
		self.add_edge(node1, node2, items)
		self.add_edge(node2, node1, items)

	def remove_edge(self, node1, node2):
		assert node1 in self.name_node, "Node does not exist: " + node1
		assert node2 in self.name_node, "Node does not exist: " + node2
		for index, edge in enumerate(self.node_edges[node1]):
			if edge.terminal == node2:
				del self.node_edges[node1][index]
				return
		assert False, "No such edge: " + node1 + " -> " + node2

	def BFS(self, node1, node2, items=set()):
		pass

	def __repr__(self):
		self_str = ""
		for node_name, edges in self.node_edges.iteritems():
			self_str += node_name + "\n"
			for edge in edges:
				self_str += "\t" + str(edge.terminal) + "\t" + str(edge.items) + "\n"
		# remove trailing \n
		return self_str[:-1]


class ConstraintEdge:

	def __init__(self, terminal, items=MinSetSet()):
		# terminal is a node name
		self.terminal = terminal
		self.items = items

class ConstraintNode:

	def __init__(self, name, data):
		self.name = name
		self.data = data

#TODO - Door, Item, and Boss should inherit from NodeData or some such type

class Door:

	def __init__(self, address, items=MinSetSet(), accessible=True, facing="L"):
		self.mem_address = address
		self.items = items
		self.accessible = accessible
		self.facing = facing

class Item:

	def __init__(self, address, item_type=""):
		self.mem_address = address
		self.type = item_type

class Boss:

	def __init__(boss_type=""):
		self.type = boss_type

class Room:

	def __init__(self, name, address, graph):
		self.name = name
		self.mem_address = address
		self.graph = graph