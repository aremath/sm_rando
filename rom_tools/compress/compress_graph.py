from .intervals import *

import heapq

class CompressGraph(object):

    def __init__(self, intervals, src):
        # key - interval : value - set of interval
        # The first interval in an edge is the destination interval
        # The second interval in an edge is the DirectCopy interval that
        # copies the information between i1 and i2
        self.adj = {}
        self.nnodes = 0
        # Add all largest intervals to the graph
        for i in intervals:
            self.add_node(i)
        #  list of node1, node1_s for fixing shorten connectivity
        shorts = []
        # Now consider shortenings and add edges
        for i1 in intervals:
            for i2 in intervals:
                # both i1 and i2 may be used if i2 starts after i1
                if i1.start < i2.start:
                    # i1 must be shortened if i2 is to start
                    if i2.start < i1.end:
                        # Shorten i1 and add it
                        i1_s = i1.shorten(i2.start)
                        self.add_node(i1_s)
                        self.chain(i1_s, i2, src)
                        shorts.append((i1, i1_s))
                    # They may both be used as-is - direct-copy the information in between.
                    else:
                        self.chain(i1, i2, src)
        # Fix up shortenings
        for i1, i2 in shorts:
            self.same_connectivity(i1, i2)

    def add_node(self, i):
        assert i not in self.adj
        self.adj[i] = set()
        self.nnodes += 1

    def add_edge(self, i1, i2):
        assert i1 in self.adj
        assert i2 in self.adj
        assert i1.end == i2.start
        self.adj[i1].add(i2)

    # if i1 starts at start, i2 starts at end,
    # chain(i1, i2) will create a path in the graph that
    # starts at start, ends at end, and encodes all the bytes
    # between start and end, by adding a direct copy for the bytes between
    # i1 and i2, if necessary.
    def chain(self, i1, i2, src):
        assert i1 in self.adj
        assert i2 in self.adj
        assert i1.end <= i2.start
        if i1.end == i2.start:
            self.add_edge(i1, i2) 
        else:
            #TODO: innefficient to build the dci if it was already in the graph.
            dci = DirectCopyInterval(i1.end, i2.start, src[i1.end:i2.start])
            if dci not in self.adj:
                self.add_node(dci)
            self.add_edge(i1, dci)
            self.add_edge(dci, i2)

    def edge_weight(self, i1,i2):
        assert i2 in self.adj[i1]
        return i2.rep

    # Nodes with an edge to i1 also gain an edge to i2
    def same_connectivity(self, i1, i2):
        assert i1 in self.adj
        assert i2 in self.adj
        for i in self.adj:
            if i1 in self.adj[i]:
                self.adj[i].add(i2)

    # Dijkstra's algorithm for finding the optimal compression
    #TODO: note that this is not actually dijkstra's algorithm!
    # It uses a heap, but does not update the entries :(
    # Same result, but n log n^2 rather than n log n
    def fake_dijkstra(self, start, end):
        # key - interval
        # value - the previous interval in the search
        offers = {}
        # key - interval
        # value - the current shortest distance from start to that interval
        current_dists = {}
        # The intervals we have processed so far
        finished = set()
        h = []
        heapq.heappush(h, (start.rep, start))
        while len(h) > 0:
            dist, pos = heapq.heappop(h)
            if pos in finished:
                continue
            finished.add(pos)
            if pos == end:
                return dist, get_path(offers, start, end)
            for e in self.adj[pos]:
                new_dist = dist + e.rep
                # Don't bother pushing if the current offer is worse than the best known distance
                if e not in current_dists or new_dist < current_dists[e]:
                    heapq.heappush(h, (new_dist, e))
                    offers[e] = pos
                    current_dists[e] = new_dist
        # No path :(
        return None

    def __repr__(self):
        s = ""
        for i1 in self.adj:
            s += str(i1) + ":\t" + str(i1.rep) + "\n"
            for i2 in self.adj[i1]:
                s += "\t" + str(i2) + "\n"
        return s

# Use offers to build a list of intervals
def get_path(offers, start, end):
    if end not in offers:
        return None
    pos = end
    path = []
    while True:
        path.append(pos)
        if pos == start:
            break
        pos = offers[pos]
    return path[::-1]

# Use a path to build a bytestring
def path_to_data(intervals):
    b = b""
    for i in intervals:
        b += i.b
    return b

