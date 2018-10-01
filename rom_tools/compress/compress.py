from .intervals import *
from .compress_graph import *

def compress(src, min_size=0, debug=False):
    # Start and end fake intervals
    start = FakeInterval(-1,0)
    end = FakeInterval(len(src),len(src)+1)
    # Compute the real intervals
    if debug:
        print("Finding byte fills")
    bf = find_bytefills(src, min_size)
    if debug:
        print("Finding word fills")
    wf = find_wordfills(src, min_size)
    if debug:
        print("Finding sigma fills")
    sf = find_sigmafills(src, min_size)
    if debug:
        print("Finding address copies")
    ac = find_address_copies(src, min_size)
    if debug:
        print("Finding address XOR copies")
    xc = find_address_xor_copies(src, min_size)
    if debug:
        print("Finding relative copies")
    rc = find_rel_address_copies(src, min_size)
    intervals = [start, end] + bf + wf + sf + ac + xc + rc
    if debug:
        print ("Found {} intervals".format(len(intervals)))
    # Filter out bad ones
    intervals = filter_worse(intervals)
    if debug:
        print("{} intervals are good".format(len(intervals)))
        print("Constructing Graph")
    # Construct the compression graph
    g = CompressGraph(intervals, src)
    if debug:
        print("Graph has {} nodes".format(g.nnodes))
    # Find the shortest path that encodes all the data
    d, p = g.fake_dijkstra(start, end)
    # Cut out the fake nodes
    p = p[1:-1]
    print(p)
    #print(d)
    return path_to_data(p) + b"\xff"

# Greedy_compress which just finds the best interval for the next bytes and is reasonably fast
def greedy_compress(src, min_size=0):
    i = 0
    last_end = 0
    interval_list = []
    while i < len(src):
        bf, _ = find_bytefill_at(src, i, min_size)
        wf, _ = find_wordfill_at(src, i, min_size)
        sf, _ = find_sigmafill_at(src, i, min_size)
        ac = find_address_copy_at(src, i, min_size)
        xc = find_address_xor_copy_at(src, i, min_size)
        rc = find_rel_address_copy_at(src, i, min_size)
        intervals = bf + wf + sf + ac + xc + rc
        # If there's an interval to choose, use the one that saves the most bytes
        if len(intervals) != 0:
            interval = choose_best_interval(intervals)
            # Directcopy the bytes before this interval starts
            if last_end < i:
                dc = DirectCopyInterval(last_end, i, src[last_end:i])
                interval_list.append(dc)
            # Add this interval to the list
            interval_list.append(interval)
            # Set the iterator to the end of the interval we just chose
            i += interval.n
            last_end = i
        # If there's no interval, update i. Next time we find an interval
        # this byte will be part of a directcopy.
        else:
            i += 1
    # In case the last thing to do is directcopy
    if last_end < i:
        dc = DirectCopyInterval(last_end, i, src[last_end:i])
        interval_list.append(dc)
    return path_to_data(interval_list) + b"\xff"

