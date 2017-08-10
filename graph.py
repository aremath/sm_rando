# all classes for implementing ConstraintGraph

from minsetset import *
import collections
from Queue import *

class ConstraintGraph(object):

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

	def add_edge(self, start, end, items=MinSetSet()):
		assert start in self.name_node, "Node does not exist: " + start
		assert end in self.name_node, "Node does not exist: " + end
		# check if an edge already exists: if it does, and their sets
		for edge in self.node_edges[start]:
			if edge.terminal == end:
				edge.items *= items
				return
		edge = ConstraintEdge(end, items)
		self.node_edges[start].append(edge)

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

	def BFS_target(self, start, end=None, items=set()):
		#TODO: is there a way to not do some of these linear-time searches?
		#TODO: review this - does it really process every combo only once?
		# key - node name
		# value - list of item sets paired with their (node, item set) predecessor
		offers = collections.defaultdict(list)

		# key - node name
		# value - list of item sets already visited for that node
		finished = collections.defaultdict(list)

		completing_set = None

		# queue to hold node, item pairs
		queue = Queue()

		queue.put((start, items))
		while queue.qsize() > 0:
			node, items = queue.get()
			# we've reached the goal with at least the right items
			if end is not None and node == end[0] and items >= end[1]:
				completing_set = items
				break
			# make an offer to every adjacent node reachable with this item set
			for edge in self.node_edges[node]:
				if edge.items.matches(items):
					# if we haven't already visited terminal with those items...
					if items not in finished[edge.terminal]:
						offers[edge.terminal].append((items, (node, items)))
						finished[edge.terminal].append(items)
						queue.put((edge.terminal, items))
			# make an offer to pick up an item or defeat a boss
			node_data = self.name_node[node].data
			if isinstance(node_data, Item) or isinstance(node_data, Boss):
				new_items = items | set([node_data.type])
				# if we haven't already visited node iwth the new item set...
				if new_items not in finished[node]:
					offers[node].append((new_items, (node, items)))
					finished[node].append(new_items)
					queue.put((node, new_items))
		return offers, finished, completing_set is not None, completing_set

	def __repr__(self):
		self_str = ""
		for node_name, edges in self.node_edges.iteritems():
			self_str += node_name + "\n"
			for edge in edges:
				self_str += "\t" + str(edge.terminal) + "\t" + str(edge.items) + "\n"
		# remove trailing \n
		return self_str[:-1]


class ConstraintEdge(object):

	def __init__(self, terminal, items=MinSetSet()):
		# terminal is a node name
		self.terminal = terminal
		self.items = items

class ConstraintNode(object):

	def __init__(self, name, data):
		self.name = name
		self.data = data

#TODO - Door, Item, and Boss should inherit from NodeData or some such type

class Door(object):

	def __init__(self, address, items=MinSetSet(), accessible=True, facing="L"):
		self.mem_address = address
		self.items = items
		self.accessible = accessible
		self.facing = facing

class Item(object):

	def __init__(self, address, item_type=""):
		self.mem_address = address
		self.type = item_type

class Boss(object):

	def __init__(self, boss_type=""):
		self.type = boss_type

class Room(object):

	def __init__(self, name, address, graph):
		self.name = name
		self.mem_address = address
		self.graph = graph

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
		stack = [start]
		node = ""
		while len(stack > 0):
			node = stack.pop()
			if end is not None and node == end:
				break
			finished |= set(node)
			for neighbor in self.node_edges[node]:
				if neighbor not in finished:
					stack.append(neighbor)
					offer[neighbor] = node

		if end is None:
			return finished
		else:
			path = []
			while node != start:
				path.append(node)
				node = offer[node]
			return path

def convert_to_basic():
	"""converts a ConstraintGraph to a BasicGraph"""
	pass
