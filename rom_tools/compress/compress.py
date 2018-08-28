from intervals import *
from compress_graph import *

def compress(src):
    start = FakeInterval(-1,0)
    end = FakeInterval(len(src),len(src)+1)
    bf = find_bytefills(src)
    wf = find_wordfills(src)
    sf = find_sigmafills(src)
    intervals = [start, end] + bf + wf + sf
    g = CompressGraph(intervals, src)
    d, p = g.fake_dijkstra(start, end)
    # cut out the fake nodes
    p = p[1:-1]
    return path_to_data(p)


