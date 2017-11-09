# Author - Aremath
# all classes for implementing ConstraintGraph
# the concept of a constraintgraph is simple - it's a normal graph, with some bells and whistles
# The edges in this graph encode constraints - the items needed to cross that edge, and they do so
# with a minsetset, which stores all minimal sets of items needed to cross that edge. In this case,
# minimal means something like pareto-minimal. A set of minimal sets will guarantee that if a set S
# is present, no superset of S is present. This is because, (with a few very rare exceptions like wrecked ship),
# in Super Metroid there are not restrictions on your movement that require you NOT to have a certain item.

# The constraintgraph nodes represent important areas in super metroid. Typically for a room, these are only
# the doors, items, and bosses present. But, for example, there is a node (like an item) for getting to the drain
# to drain the acid lake in lower norfair. This is because you can't return through that area until you drain the lake,
# even if you enter the room from the bottom door.

# The concept of searching a constraintgraph must then search the space of possible nodes (as with a normal search), but
# also search the space of possible items. Being at Landing_Site_L2 with missiles is different from being at Landing_Site_L2
# with power bombs because it allows you to cross different edges in the graph.

# each room can be represented by a constraintgraph (see encoding/rooms.txt for the definitions), but so can the entire map,
# with edges between rooms indicating a door transition - typically two edges, each requiring the items for their respective door

# In this way we can search in "linear" time (worst-case exponential in the number of item sets, but SM has a constant (but high)
# number of items), and find whether a given map is completable! Completability can be defined in many ways, but I normally use this:
# There is a path from Landing site with no items to Golden Statues with all items, and a path from the end of escape with all items 
# to the landing site. It's possible to choose a much more relaxed version of completability - that is, you can find enough ammo to beat
# mother brain, and there's a path to escape. The problem with this is that I use Sets to represent items it is relatively hard to 
# calculate the number of missiles, energy tanks, etc. that you can obtain. The main idea, though, is that if you can access all items,
# you can cross every edge and obtain every* item. 
# * except the Main Street missiles if you can't do that shortcharge. My encoding makes no edges to that item, for this reason.

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

        def is_edge(node1, node2):
            """is there an edge from node1 to node2?"""
            assert node1 in self.name_node, "Node does not exist: " + node1
            assert node2 in self.name_node, "Node does not exist: " + node2
            for edge in self.node_edges[node1]:
                if edge.terminal == node2:
                    return True
            return False

	def remove_node(self, node):
		assert node in self.name_node, "Node does not exist: " + node
		del self.name_node[node]
		del self.node_edges[node]
		indices_to_remove = {}
		# find all edges to node
		for inode, edges in self.node_edges.items():
			for index, edge in enumerate(edges):
				if edge.terminal == node:
					indices_to_remove[inode] = index
		# remove them
		for inode, index in indices_to_remove.items():
			del self.node_edges[inode][index]

	def BFS_optimized(self, start, end=None, items=set()):
		"""I don't care about every possible way to get everywhere -
		just BFS until you find end, noting that picking up items is
		always beneficial."""

		def already_finished(item_set, sets_finished):
			"""have we already looked at this node with a superset of those items?"""
			for set_finished in sets_finished:
				if item_set <= set_finished:
					return True
			return False

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
			items = items.copy()
			# we've reached the goal with at least the right items
			if end is not None and node == end[0] and items >= end[1]:
				completing_set = items
				break
			# make an offer to pick up an item or defeat a boss
			node_data = self.name_node[node].data
			if isinstance(node_data, Item) or isinstance(node_data, Boss):
				new_items = items | set([node_data.type])
				# if we haven't already visited this node with the new item set...
				if not already_finished(new_items, finished[node]):
					offers[node].append((new_items, (node, items)))
					finished[node].append(new_items)
					# don't have to make a new queue item - pick up the item/boss is the only option
					# the following for-loop handles creating the new queue items...
					items = new_items
			# make an offer to every adjacent node reachable with this item set
			for edge in self.node_edges[node]:
				if edge.items.matches(items):
					# if we haven't already visited terminal with those items...
					if not already_finished(items, finished[edge.terminal]):
						offers[edge.terminal].append((items, (node, items)))
						finished[edge.terminal].append(items)
						queue.put((edge.terminal, items))	
		return offers, finished, completing_set is not None, completing_set

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
			items = items.copy()
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
				# if we haven't already visited this node with the new item set...
				if new_items not in finished[node]:
					offers[node].append((new_items, (node, items)))
					finished[node].append(new_items)
					queue.put((node, new_items))
		return offers, finished, completing_set is not None, completing_set

	def BFS_items(self, start, end=None, wildcards=set(), items=set(), assignments={}, fixed_items=set()):
		"""Finds a satsifying assignment of items to reach end from start. finished[end] will wind up with
		a list of (unassigned but reached items, item set needed, and possible item assignments). Each assignment
		is a dictionary, where key = item node name, and value = string value for item assigned there. Currently does
		not allow items to be fixed, but an already-assigned items dictionary can be passed, and if every item there is in
		items, then the behavior should be correct."""

		#TODO: I think there's a way to make finished store less stuff - after all, we are only interested in keeping the
		# elements with a maximal number of wildcards for each item set.

		#TODO: do we need offers? - just interested in finding a completable assignment
		# key - node name
		# value - list of 
		#offers = collections.defaultdict(list)

		# key - node name
		# value - tuples of (wildcards), (item set), (assignment)
		finished = collections.defaultdict(list)

		# what items we actually needed to reach the end...
		completing_set = None

		queue = Queue()

		# queue search terms are:
		#	- node name
		#	- wildcard set
		#	- item set
		#	- assignment dictionary - key: item node, value: type assigned there
		# however two search terms are equal if the number of wildcards and the
		# obtained items are the same - that's why finished just includes the number
		# - add start node to the finished list
		finished[start].append((wildcards.copy(), items.copy(), assignments.copy()))
		queue.put((start, wildcards, items, assignments))
		while queue.qsize() > 0:
			node, wildcards, items, assignments = queue.get()
			#print node, len(wildcards), len(items)
			node_data = self.name_node[node].data
			if end is not None and node == end:
				completing_set = items
				break
			if isinstance(node_data, Item):
				# if we don't already have this item, pick it up
				if node not in wildcards and node not in assignments:
					wildcards.add(node)
					# if there's not already an entry for this item set with at least as many wildcards, then add it
					if len([x for x in finished[node] if len(x[0]) >= len(wildcards) and x[1] >= items]) == 0:
						finished[node].append((wildcards.copy(), items.copy(), assignments.copy()))
						queue.put((node, wildcards.copy(), items.copy(), assignments.copy()))
					# there's no need to process edges - picking up that item will allow you to cross strictly more edges
					continue
			elif isinstance(node_data, Boss):
				# if we haven't defeated this boss yet, do so.
				if node_data.type not in items:
					items |= set([node_data.type])
					finished[node].append((wildcards.copy(), items.copy(), assignments.copy()))
					queue.put((node, wildcards.copy(), items.copy(), assignments.copy()))
					# there's no need to process edges - defeating that boss will allow you to cross strictly more edges
					continue
			# now cross edges
			for edge in self.node_edges[node]:

				# for each set, use some wildcards to cross it, then add that node with those assignments to the queue
				for item_set in edge.items.sets:
					# items in item set that we don't already have
					need_items = item_set - items
					# if we have enough wildcards to satisfy need_items and there are no fixed items that we do not already have
					if len(need_items) <= len(wildcards) and len(need_items & fixed_items) == 0:
						wildcards_copy = wildcards.copy()
						items_copy = items.copy()
						assignments_copy = assignments.copy()
						# make an assignment that allows crossing that edge
						for item in need_items:
							wildcard = wildcards_copy.pop()
							assignments_copy[wildcard] = item
							items_copy.add(item)
						# if there's not already an entry for this item set with at least as many wildcards, then add it
						if len([x for x in finished[edge.terminal] if len(x[0]) >= len(wildcards) and x[1] >= items]) == 0:
							# make sure finished has different pointers than queue!
							finished[edge.terminal].append((wildcards_copy.copy(), items_copy.copy(), assignments_copy.copy()))
							queue.put((edge.terminal, wildcards_copy, items_copy, assignments_copy))

		return finished, completing_set is not None, completing_set

	def add_room(self, door1, door2, room_graph):
		"""adds a room to self, connecting door1 in self to door2 in room_graph"""
		assert door1 in self.name_node, door1
		assert door2 in room_graph.name_node, door2

		for node_name, node in room_graph.name_node.items():
			self.add_node(node_name, node.data)
		for node_name, node_edges in room_graph.node_edges.items():
			for edge in node_edges:
				self.add_edge(node_name, edge.terminal, edge.items)

		# connect up the two doors!
		door1_data = self.name_node[door1].data
		door2_data = self.name_node[door2].data
		# none means an impassable door
		if door1_data.items is not None:
			self.add_edge(door1, door2, door1_data.items)
		if door2_data.items is not None:
			self.add_edge(door2, door1, door2_data.items)

	def copy(self):
		"""returns a copy of self - pointers to data might still be entangled"""
		new_graph = ConstraintGraph()
		for node_name, node in self.name_node.items():
			new_graph.add_node(node_name, node.data)
		for node_name, node_edges in self.node_edges.items():
			for edge in node_edges:
				new_graph.add_edge(node_name, edge.terminal, edge.items)
		return new_graph

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
