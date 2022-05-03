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
# mother brain, and there's a path to escape. The problem with this is that sets represent the items you have and it is hard to 
# calculate the number of missiles, energy tanks, etc. that you can obtain. The main idea, though, is that if you can access all items,
# you can cross every edge and obtain every* item. 
# * except the Main Street missiles if you can't do that shortcharge. My encoding makes no edges to that item, for this reason.

import collections
import random

from data_types.minsetset import MinSetSet
from data_types.item_set import ItemSet
from data_types.orderedset import OrderedSet

infinity = float("inf")

#TODO: now that node, item set are both hashable... hash this?
#TODO: alter graph so that the edge list is part of the node data structure?
#TODO: alter graph so that node ID is an index into the graph? (faster hashing?)
# I wish Python had abstract data types :(
class BFSState(object):

    def __init__(self, node_, items_=ItemSet()):
        self.node = node_
        self.items = items_
    
    def copy(self):
        return BFSState(self.node, self.items.copy())

    def __eq__(self, other):
        return self.node == other.node and self.items == other.items

    def __le__(self, other):
        return self.node == other.node and self.items <= other.items

    def __lt__(self, other):
        return self.node == other.node and self.items < other.items

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return self.node + "\n" + str(self.items) + "\n"

class BFSItemsState(object):

    #TODO: argument order??
    def __init__(self, node_, wildcards_=OrderedSet(), items_=ItemSet(), assignments_={}):
        self.node = node_
        self.items = items_
        self.wildcards = wildcards_
        self.assignments = assignments_

    def copy(self):
        return BFSItemsState(self.node, self.wildcards.copy(), self.items.copy(), self.assignments.copy())

    # Two states are equal if they can cross the same set of edges
    def __eq__(self, other):
        return self.node == other.node and self.items == other.items and len(self.wildcards) == len(other.wildcards)

    # An item set is leq another if it has at most the same items and at most the same number of wildcards
    def __le__(self, other):
        return self.node == other.node and self.items <= other.items and len(self.wildcards) <= len(other.wildcards)

    # Strictly less than means also either strictly fewer items or strictly fewer wildcards (or both)
    def __lt__(self, other):
        return self <= other and (self.items < other.items or len(self.wildcards) < len(other.wildcards))

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return self.node + "\n\t" + str(self.items) + "\n\t" + str(self.wildcards) + "\n"

    # Only the number of wildcards matters
    def __hash__(self):
        return hash((self.node, len(self.wildcards), self.items))

    # Does other make progress relative to self?
    # If it's at another node with maybe better items
    # Or if it's at the same node with strictly better items
    #TODO: this isn't right?
    def is_progress(self, other):
        return self < other or (self.node != other.node and self.items <= other.items and len(self.wildcards) + len(self.items) <= len(other.wildcards) + len(other.items))
    # A node is progress if it's the same node with either more items or more wildcards
    # Or it's a different node with at least the same items
    # And the total number of items and wilcards is at least as large.

#TODO: have graph implement __getitem__ instead of the clunky name_nodes
# + maybe merge so that the node's edges are part of the node class?
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

    def is_edge(self, node1, node2):
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
        # remove them (can't mutate during iteration)
        for inode, index in indices_to_remove.items():
            del self.node_edges[inode][index]

    def BFS_optimized(self, start_state, end_state=None, edge_pred=lambda x: True):
        """I don't care about every possible way to get everywhere -
        just BFS until you find end, noting that picking up items is
        always beneficial."""
        n = 0

        # key - node name
        # key - item set
        # value - state predecessor
        offers = collections.defaultdict(lambda: {})

        # key - node_name
        # value - set of item sets
        finished = collections.defaultdict(set)

        final_state = None

        # queue to hold node, item pairs
        queue = [start_state]

        while len(queue) > 0:
            n += 1
            state = queue.pop(0).copy()
            #if n % 10000 == 0:
            #    print(n)
            #    print(state)
            node = state.node
            items = state.items
            # we've reached the goal with at least the right items
            if end_state is not None and state >= end_state:
                final_state = state
                break
            # make an offer to pick up an item or defeat a boss
            node_data = self.name_node[node].data
            if isinstance(node_data, Item) or isinstance(node_data, Boss):
                new_items = items | ItemSet([node_data.type])
                # if we haven't already visited this node with the new item set...
                if new_items not in finished[node]:
                    offers[node][new_items] = state.copy()
                    finished[node].add(new_items)
                    # don't have to make a new queue item - pick up the item/boss is the only option
                    # the following for-loop handles creating the new queue items...
                    items = new_items
            # make an offer to every adjacent node reachable with this item set
            for edge in self.node_edges[node]:
                if edge.items.matches(items) and edge_pred((node, edge.terminal)):
                    # if we haven't already visited terminal with those items...
                    if items not in finished[edge.terminal]:
                        offers[edge.terminal][items] = state.copy()
                        finished[edge.terminal].add(items)
                        queue.append(BFSState(edge.terminal, items))       
        return offers, finished, final_state is not None, final_state

    def BFS_target(self, start_state, end_state=None):
        #TODO: review this - does it really process every combo only once?
        # key - node name
        # key - item set
        # value - state predecessor
        offers = collections.defaultdict(lambda: {})

        # key - node name
        # value - item set
        finished = collections.defaultdict(set)

        final_state = None

        # queue to hold node, item pairs
        queue = [start_state]

        while len(queue) > 0:
            state = queue.pop(0).copy()
            # we've reached the goal with at least the right items
            if end_state is not None and start_state >= end_state:
                final_state = state
                break
            node = state.node
            items = state.items
            # make an offer to every adjacent node reachable with this item set
            for edge in self.node_edges[node]:
                if edge.items.matches(items):
                    # if we haven't already visited terminal with those items...
                    if items not in finished[edge.terminal]:
                        offers[edge.terminal][items] = state
                        finished[edge.terminal].add(items)
                        queue.append(BFSState(edge.terminal, items))
            # make an offer to pick up an item or defeat a boss
            node_data = self.name_node[node].data
            if isinstance(node_data, Item) or isinstance(node_data, Boss):
                new_items = items | ItemSet([node_data.type])
                # if we haven't already visited this node with the new item set...
                if new_items not in finished[node]:
                    offers[node][new_items] = state
                    finished[node].add(new_items)
                    queue.append(BFSState(node, new_items))
        return offers, finished, final_state is not None, final_state

    def BFS_items(self, start_state, end_state=None, fixed_items=ItemSet()):
        """Finds a satsifying assignment of items to reach end from start. finished[end] will wind up with
        a list of (unassigned but reached items, item set needed, and possible item assignments). Each assignment
        is a dictionary, where key = item node name, and value = string value for item assigned there. Currently does
        not allow items to be fixed, but an already-assigned items dictionary can be passed."""

        #TODO: I think there's a way to make finished store less stuff - after all, we are only interested in keeping the
        # elements with a maximal NUMBER of wildcards for each item set.
        # Set of BFSItemsState
        # Ordered so that you can randomly choose from it without relying
        # on the internal hash function which is randomly salted.
        finished = OrderedSet()

        # Key - BFSItemsState (antecessor)
        # Value - BFSItemsState (predecessor)
        offers = {}

        # what items we actually needed to reach the end...
        final_state = None

        queue = [start_state]

        # queue search terms are:
        #       - node name
        #       - wildcard set
        #       - item set
        #       - assignment dictionary - key: item node, value: type assigned there
        # however two search terms are equal if the number of wildcards and the
        # obtained items are the same - that's why finished just includes the number
        # - add start node to the finished list
        #finished[start_state.node][start_state.items].append((start_state.wildcards.copy(), start_state.assignments.copy()))
        finished.add(start_state)
        while len(queue) > 0:
            state = queue.pop(0)
            #print("State: {}".format(state))
            node = state.node
            wildcards = state.wildcards
            items = state.items
            assignments = state.assignments
            if end_state is not None and state >= end_state:
                final_state = state
                break
            node_data = self.name_node[node].data
            # In addition to fixed items, pass an assigments list and check it
            if isinstance(node_data, Item):
                # If we don't already have this item, pick it up as a wildcard
                if node not in wildcards and node not in assignments:
                    new_state = BFSItemsState(node, wildcards | set([state.node]), items, assignments)
                    if new_state not in finished:
                        finished.add(new_state)
                        offers[new_state] = state
                        queue.append(new_state)
                    # There's no need to process edges - picking up that item won't prevent you from crossing an edge
                    continue
                # If we don't have the item but it was already assigned, pick it up as a fixed item
                elif node in assignments and assignments[node] not in items:
                    new_state = BFSItemsState(node, wildcards, items | ItemSet([assignments[node]]), assignments)
                    if new_state not in finished:
                        finished.add(new_state)
                        offers[new_state] = state
                        queue.append(new_state)
                    continue
            elif isinstance(node_data, Boss):
                # If we haven't defeated this boss yet, do so (as a fixed item)
                if node_data.type not in items:
                    new_state = BFSItemsState(node, wildcards, items | ItemSet([node_data.type]), assignments)
                    if new_state not in finished:
                        finished.add(new_state)
                        offers[new_state] = state
                        queue.append(new_state)
                    # There's no need to process edges - defeating that boss will allow you to cross strictly more edges
                    continue
            # Now cross edges
            for edge in self.node_edges[state.node]:
                # For each set, use some wildcards to cross it, then add that node with those assignments to the queue
                for item_set in edge.items.sets:
                    # Items in item set that we don't already have
                    need_items = item_set - items
                    #print("Need items: {}".format(need_items))
                    # Can cross the edge if we have enough wildcards to satisfy need_items and there are no fixed items that we do not already have (i.e. bosses)
                    if len(need_items) <= len(wildcards) and len(need_items & fixed_items) == 0:
                        #print("Can cross")
                        wildcards_copy = wildcards.copy()
                        items_copy = state.items.copy()
                        assignments_copy = assignments.copy()
                        # Make an assignment that allows crossing that edge
                        for item in need_items:
                            # Get the last available wildcard -> the latest one the player got.
                            wildcard = wildcards_copy.pop()
                            assignments_copy[wildcard] = item
                            items_copy = items_copy.add(item)
                        new_state = BFSItemsState(edge.terminal, wildcards_copy, items_copy, assignments_copy)
                        #print("Items: {}, wildcards: {}".format(items_copy, wildcards_copy))
                        # If there's not already an entry for this item set with at least as many wildcards, then add it
                        if new_state not in finished:
                            finished.add(new_state)
                            offers[new_state] = state
                            queue.append(new_state)
        return offers, finished, final_state is not None, final_state

    #TODO: is this really useful?
    def check_completability(self, start_state, end_state):
        """given a room graph, determine if it is possible to reach (end_node, end_items) from (start_node, start_items)
          if it is, return the paths"""
        bfs_offers, bfs_finished, bfs_found, bfs_set = self.BFS_optimized(start_state, end_state)
        if not bfs_found:
            return None
        else:
            return bfs_backtrack(start_state, end_state, bfs_offers)

    # Ford-Fulkerson algorithm for given edge weights
    def network_flow(self, edge_weights, source, sink, items=ItemSet()):
        assert source in self.name_node
        assert sink in self.name_node
        # Edge weights is (node1, node2) -> non-negative float
        current_edge_weights = edge_weights.copy()
        start_state = BFSState(source, items)
        # TODO: can you pick up new items during the search?
        # TODO: is it correct to use BFS_optimized when we wish not to collect items?
        end_state = BFSState(sink, items)
        # Both refer to the (mutable) current edge weights
        edge_inf = lambda x: current_edge_weights[x] == infinity
        edge_nonzero = lambda x: current_edge_weights[x] > 0
        # Check if there is a path of weight infinity from source to sink
        _, _, inf_path, _ = self.BFS_optimized(start_state, end_state, edge_pred=edge_inf)
        if inf_path:
            # No cut is possible since every cut has infinite weight
            return infinity, None
        # If there is no inf_path, then there is a finite-weight cut
        iteration = 0
        while True:
            iteration += 1
            o, f, p, _ = self.BFS_optimized(start_state, end_state, edge_pred=edge_nonzero)
            # No nonzero path means a cut has been found
            if not p:
                break
            # If there is a nonzero path, create regret along it
            path = bfs_backtrack(start_state, end_state, o)
            # List because we are going to re-use it
            path_pairs = list(zip(path, path[1:]))
            # The smallest edge limits the amount of possible flow
            regret = min([current_edge_weights[(u,v)] for u,v in path_pairs])
            # Update the edge weights with the regret:
            #TODO: assumes current_edge_weights is complete
            for u,v in path_pairs:
                current_edge_weights[(u,v)] -= regret
                current_edge_weights[(v,u)] += regret
        # Find the cut by first finding the nodes reachable from the source
        _, f, _, _ = self.BFS_optimized(start_state, edge_pred=edge_nonzero)
        source_nodes = set(f.keys())
        # All the edges which cross the boundary
        cut_edges = [(u, v.terminal) for u in source_nodes
                for v in self.node_edges[u] if v.terminal not in source_nodes]
        total_cut_weight = sum([edge_weights[e] for e in cut_edges])
        return total_cut_weight, cut_edges

    #TODO: check for node name overlaps?
    def add_subgraph(self, other):
        for node_name, node in other.name_node.items():
            self.add_node(node_name, node.data)
        for node_name, node_edges in other.node_edges.items():
            for edge in node_edges:
                self.add_edge(node_name, edge.terminal, edge.items)

    def connect_doors(self, door1, door2):
        assert door1 in self.name_node, door1
        assert door2 in self.name_node, door2
        # connect up the two doors!
        door1_data = self.name_node[door1].data
        door2_data = self.name_node[door2].data
        # none means an impassable door
        if door1_data.items is not None:
            self.add_edge(door1, door2, door1_data.items)
        if door2_data.items is not None:
            self.add_edge(door2, door1, door2_data.items)

    def add_room(self, door1, door2, room_graph):
        """adds a room to self, connecting door1 in self to door2 in room_graph"""
        assert door1 in self.name_node, door1
        assert door2 in room_graph.name_node, door2
        self.add_subgraph(room_graph)
        self.connect_doors(door1, door2)

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
        for node_name, edges in self.node_edges.items():
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

    def __init__(self, name, address, graph, doors, item_nodes):
        self.name = name
        self.mem_address = address
        self.graph = graph
        self.doors = doors
        self.item_nodes = item_nodes

#TODO: fix this for normal offers
# offers:
# key - node
# key - item set
# value - state predecessor
def bfs_backtrack(start_state, end_state, bfs_offers):
    """Backtracks BFS offers to find the target node. Errors if the target node wasn't in the search.
       Intended for use with BFS_opt and BFS_target."""
    path = []
    # since BFS only guarantees that end_state items will be a superset of items, pick an offer for end_node that matches
    ending_states = [BFSState(end_state.node, items) for items in bfs_offers[end_state.node].keys() if items >= end_state.items]
    assert len(ending_states) > 0, "Backtrack: no path to reach " + end_state.node
    state = ending_states[0]
    # loop from the end state until we reach the start state
    while state != start_state:
        path.insert(0, state.node)
        # get all the offers for the current state
        state =  bfs_offers[state.node][state.items]
    # put the current node (which is the start node) now that we've reached it
    path.insert(0, state.node)
    return path

def bfs_items_backtrack(start_state, end_state, bfs_offers):
    """Backtracks BFS offers for BFS_items."""
    path = []
    state = end_state
    while state != start_state:
        path.insert(0, state)
        try:
            state = bfs_offers[state]
        # Because of the weird hashing function for BFSItemsStates, 
        # it is possible that there is a matching (equal) state that does not hash the same
        # In this case, we assume the offer came from the equal state.
        except KeyError:
            preds = [v for (k,v) in bfs_offers.items() if k == state]
            state = preds[0]
    # Put the current node (which is the start state) now that we've reached it
    path.insert(0, state)
    return path

