from intervals import *

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
        # Now consider shortenings and add edges
        for i1 in intervals:
            for i2 in intervals:
                # both i1 and i2 may be used if i2 starts after i1
                if i1.start < i2.start:
                    # i1 must be shortened if i2 is to start
                    if i2.start < i1.end:
                        #TODO
                        # Shorten i1 and add it
                        # chain i1_s and i2
                        pass
                    # They may both be used as-is - direct-copy the information in between.
                    # TODO: building the dci here is innefficient if it goes unused
                    else:
                        self.chain(i1, i2, src)
        #TODO: add nodes start and end!

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
            dci = DirectCopyInterval(i1.end, i2.start, src[i1.end:i2.start])
            if dci not in self.adj:
                self.add_node(dci)
            self.add_edge(i1, dci)
            self.add_edge(dci, i2)

    def edge_weight(self, i1,i2):
        assert i2 in self.adj[i1]
        return i2.rep

    # Dijkstra's algorithm for finding the optimal compression
    #TODO: note that this is not actually dijkstra's algorithm!
    # It uses a heap, but does not update the entries :(
    # Same result, but n log n^2 rather than n log n
    def fake_dijkstra(self, start, end):
        # key - interval
        # value - the previous interval in the search
        offers = {} 
        # The intervals we have processed so far
        finished = set()
        h = []
        heapq.heappush(h, (0, start))
        while len(h) > 0:
            dist, pos = heapq.heappop(h)
            if pos in finished:
                continue
            finished.add(pos)
            if pos == end:
                return dist, get_path(offers, start, end)
            for e in self.adj[pos]:
                if e not in finished:
                    heapq.heappush(h, (dist + e.rep, e))
                    offers[e] = pos
        # No path :(
        return None

    def __repr__(self):
        s = ""
        for i1 in self.adj:
            s += str(i1) + "\n"
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

def path_to_data(intervals):
    b = b""
    for i in intervals:
        b += i.b
    return b

