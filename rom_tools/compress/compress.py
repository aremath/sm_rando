from . import intervals
from . import compress_graph

def find_all_intervals(src, min_size, debug):
    # Compute the real intervals
    if debug:
        print("Finding byte fills")
    bf = intervals.find_bytefills(src, min_size)
    if debug:
        print("Finding word fills")
    wf = intervals.find_wordfills(src, min_size)
    if debug:
        print("Finding sigma fills")
    sf = intervals.find_sigmafills(src, min_size)
    if debug:
        print("Finding address copies")
    ac = intervals.find_address_copies(src, min_size)
    if debug:
        print("Finding address XOR copies")
    xc = intervals.find_address_xor_copies(src, min_size)
    if debug:
        print("Finding relative copies")
    rc = intervals.find_rel_address_copies(src, min_size)
    intervals = bf + wf + sf + ac + xc + rc
    if debug:
        print ("Found {} intervals".format(len(intervals)))
    # Filter out bad ones
    intervals = intervals.filter_worse(intervals)
    if debug:
        print("{} intervals are good".format(len(intervals)))
    return intervals

def optimal_compress(src, min_size=0, debug=False):
    # Start and end fake intervals
    start = intervals.FakeInterval(-1,0)
    end = intervals.FakeInterval(len(src),len(src)+1)
    intervals = [start, end] + find_all_intervals(src, min_size, debug)
    if debug:
        print("Constructing Graph")
    # Construct the compression graph
    g = compress_graph.CompressGraph(intervals, src)
    if debug:
        print("Graph has {} nodes".format(g.nnodes))
    # Find the shortest path that encodes all the data
    d, p = g.fake_dijkstra(start, end)
    # Cut out the fake nodes
    p = p[1:-1]
    print(p)
    #print(d)
    return compress_graph.path_to_data(p) + b"\xff"

def merge_compress(src, min_size=2, debug=False):
    assert min_size > 0
    intervals = find_all_intervals(src, min_size, debug)
    return path_to_data(recursive_merge_compress(src, min_size, 0, len(src), intervals)) + b"\xff"

def crosses(interval, index):
    return index >= interval.start and index < interval.end

# Does not work very well currently -- no shortens.
# also not verified to be correct.
def recursive_merge_compress(src, min_size, lb, ub, intervals):
    # Base Case
    if ub - lb <= min_size:
        return [intervals.DirectCopyInterval(lb, ub, src[lb:ub])]
    # Choose the largest interval that crosses the center
    center = lb + (ub - lb)//2
    candidates = list(filter(lambda i: crosses(i, center) and i.start >= lb and i.end <= ub, intervals))
    if len(candidates) > 0:
        best = intervals.choose_best_interval(candidates)
        before = list(filter(lambda i: i.end <= best.start, intervals))
        after = list(filter(lambda i: i.start > best.end, intervals))
        #TODO: Add shortens to before and after
        if best.start == lb:
            lhs = []
        else:
            lhs = recursive_merge_compress(src, min_size, lb, best.start, before)
        if ub == best.end:
            rhs = []
        else:
            rhs = recursive_merge_compress(src, min_size, best.end, ub, after)
        return lhs + [best] + rhs
    else:
        before = list(filter(lambda i: i.start < center, intervals))
        after = list(filter(lambda i: i.end > center, intervals))
        lhs = recursive_merge_compress(src, min_size, lb, center, before)
        rhs = recursive_merge_compress(src, min_size, center, ub, after)
        # Fix up adjacent direct copies by combining them
        # There won't be adjacent of other intervals because otherwise the first case would be used.
        lastl = lhs[-1]
        firstr = rhs[0]
        if isinstance(lastl, intervals.DirectCopyInterval) and isinstance(firstr, intervals.DirectCopyInterval) \
                and lastl.end == firstr.start:
            new = intervals.DirectCopyInterval(lastl.start, firstr.end, (lastl.cpy_bytes + firstr.cpy_bytes))
            return lhs[:-1] + [new] + rhs[1:]
        else:
            return lhs + rhs

# Greedy_compress which just finds the best interval for the next bytes and is reasonably fast
# TODO: buggy for min_size < 2?
def greedy_compress(src, min_size=2, debug=False):
    i = 0
    last_end = 0
    interval_list = []
    while i < len(src):
        bf, _ = intervals.find_bytefill_at(src, i, min_size)
        if debug and len(bf) > 0:
            print(bf[0])
        wf, _ = intervals.find_wordfill_at(src, i, min_size)
        if debug and len(wf) > 0:
            print(wf[0])
        sf, _ = intervals.find_sigmafill_at(src, i, min_size)
        if debug and len(sf) > 0:
            print(sf[0])
        ac = intervals.find_address_copy_at(src, i, min_size)
        if debug and len(ac) > 0:
            print(ac[0])
        xc = intervals.find_address_xor_copy_at(src, i, min_size)
        if debug and len(xc) > 0:
            print(xc[0])
        rc = intervals.find_rel_address_copy_at(src, i, min_size)
        if debug and len(rc) > 0:
            print(rc[0])
        intervals = bf + wf + sf + ac + xc + rc
        # If there's an interval to choose, use the one that saves the most bytes
        if len(intervals) != 0:
            interval = intervals.choose_best_interval(intervals)
            # Directcopy the bytes before this interval starts
            if last_end < i:
                dc = intervals.DirectCopyInterval(last_end, i, src[last_end:i])
                if debug:
                    print("Using: " + str(dc))
                    print(src[dc.start:dc.end])
                interval_list.append(dc)
            # Add the interval that we decided to use to the list
            if debug:
                print("Using: " + str(interval))
                print(interval.b)
                print(src[interval.start:interval.end])
            # Add this interval to the list
            interval_list.append(interval)
            # Set the iterator to the end of the interval we just chose
            i += interval.n
            last_end = i
        # If there's no interval, update i. Next time we find an interval
        # this byte will be part of a directcopy.
        else:
            i += 1
        if debug:
            print("")
    # In case the last thing to do is directcopy
    if last_end < i:
        dc = intervals.DirectCopyInterval(last_end, i, src[last_end:i])
        interval_list.append(dc)
    return compress_graph.path_to_data(interval_list) + b"\xff"

