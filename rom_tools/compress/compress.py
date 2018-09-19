from .intervals import *
from .compress_graph import *

def compress(src):
    # Start and end fake intervals
    start = FakeInterval(-1,0)
    end = FakeInterval(len(src),len(src)+1)
    # Compute the real intervals
    bf = find_bytefills(src)
    wf = find_wordfills(src)
    sf = find_sigmafills(src)
    ac = find_address_copies(src)
    xc = find_address_xor_copies(src)
    rc = find_rel_address_copies(src)
    intervals = [start, end] + bf + wf + sf + ac + xc + rc
    # Filter out bad ones
    intervals = filter_worse(intervals)
    # Construct the compression graph
    g = CompressGraph(intervals, src)
    #print(g)
    # Find the shortest path that encodes all the data
    d, p = g.fake_dijkstra(start, end)
    # Cut out the fake nodes
    p = p[1:-1]
    print(p)
    #print(d)
    return path_to_data(p) + b"\xff"

