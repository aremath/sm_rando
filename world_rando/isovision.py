import numpy as np
import math
import random
from math import copysign
from itertools import combinations
from collections import defaultdict
from heapdict import heapdict

from world_rando.coord import *
from world_rando.room_gen import coord_set_border


def iter2d(array):
    for x in range(array.shape[0]):
        for y in range(array.shape[1]):
            yield Coord(x,y)

def mk_is_air(level_array):
    #TODO What about hcopy and vcopy, crumble grapple??
    solid_ttypes = set([3,8,10,14])
    is_air = np.zeros(level_array.shape)
    it = np.nditer(level_array, flags=["multi_index", "refs_ok"])
    for x in it:
        if level_array[it.multi_index].tile_type in solid_ttypes:
            is_air[it.multi_index] = -1
        else:
            is_air[it.multi_index] = 1
    return is_air

calc_ds = [up,down,left,right]
calc_ds_diags = [up, down, left, right, Coord(1,1), Coord(1,-1), Coord(-1,1), Coord(-1,-1)]

def get_directions(diags):
    if diags:
        return calc_ds_diags
    else:
        return calc_ds

def inbounds(c, array):
    s = array.shape
    return c.x >= 0 and c.y >= 0 and c.x < s[0] and c.y < s[1]

def calc_line_length(idx, direction, array):
    count = 0
    tty = array[idx]
    id2 = idx + direction
    # Bounds
    while inbounds(id2, array) and array[id2] == array[idx]:
        count += 1
        id2 += direction
    return count

def calc_openness(idx, array, diags=True):
    c = 0
    for d in get_directions(diags):
    #for d in [up, down, left, right]:
        c += calc_line_length(idx, d, array)
    # An air block surrounded by solids has openness 1, and vice versa -1.
    c += 1
    return c

#TODO: test using the median instead
def calc_openness_max(idx, array, diags=True):
    c = []
    for d in get_directions(diags):
        c.append(calc_line_length(idx, d, array))
    return max(c)

#TODO: test cutting off the max openness from each direction

# Cheap rasterization using random walks
# Idea: choose an angle theta at random
# Think of the line starting at the origin with angle theta
# |cos(theta)| / |cos(theta) + sin(theta)| is the proportion of horizontal movement along this line
# and |sin(theta)... is the proportion of vertical movement
# Well, this is a cool idea but has different amounts of error for different angles

# Instead, iterate over squares touched by the ray using a different idea
# This doesn't yield the first position (as desired -- we don't want to multi-count it)
#TODO: this can skip some cells depending on the scale factor -- if new_int_pos - int_pos has multiple 1s, then need to find which cell was hit first...
def ray_iter(pos, angle, scale=0.4):
    int_pos = pos
    #pos = pos + Coord(0.5, 0.5)
    pos = pos + Coord(random.random(), random.random())
    dt = Coord(math.cos(angle), math.sin(angle)).scale(scale)
    while True:
        pos = pos + dt
        new_int_pos = Coord(int(pos.x), int(pos.y))
        if new_int_pos != int_pos:
            yield new_int_pos
            int_pos = new_int_pos
            
def calc_ray_length(idx, angle, array):
    count = 0
    tty = array[idx]
    for pos in ray_iter(idx, angle):
        if not inbounds(pos, array) or array[pos] != array[idx]:
            break
        count += 1
    return count

def calc_openness_raster_r(idx, array, n_iters=100):
    c = 0
    for i in range(n_iters):
        angle = 2 * math.pi * random.random()
        rl = calc_ray_length(idx, angle, array)
        c += rl
    c = (c / n_iters) + 1
    return c

# Better version that calculates the openness more accurately
def calc_openness_raster(idx, array, n_iters=200):
    c = 0
    tpi = 2*math.pi
    start = random.random() * tpi
    for i in np.linspace(0, tpi, num=n_iters):
        angle = (start + i) % tpi
        rl = calc_ray_length(idx, angle, array)
        c += rl
    c = (c / n_iters) + 1
    return c

calc_open_raster_300 = lambda x,y: calc_openness_raster(x, y, n_iters=300)

def calc_ray(idx, angle, array):
    ray = set()
    tty = array[idx]
    for pos in ray_iter(idx, angle):
        if not inbounds(pos, array) or array[pos] != array[idx]:
            break
        ray.add(pos)
    return ray

def calc_visible(idx, array, n_iters=200):
    vis = set([idx])
    tpi = 2 * math.pi
    start = random.random() * tpi
    for i in np.linspace(0, tpi, num=n_iters):
        angle = (start + i) % tpi
        vis |= calc_ray(idx, angle, array)
    return vis

# Symmetric set difference
def ssd(a,b):
    return (len(a-b) + len(b-a))

def normalized_ssd(a, b):
    return (len(a-b) + len(b-a)) / len(a | b)

def mk_visibles(is_air):
    visibles = {}
    for c in iter2d(is_air):
        visibles[c] = calc_visible(c, is_air)
    return visibles
        
def mk_airs(is_air):
    airs = set()
    for c in iter2d(is_air):
        if is_air[c] == 1:
            airs.add(c)
    return airs
            
def mk_ssds(is_air, airs, visibles):
    ssds = np.zeros_like(is_air)
    for c in iter2d(is_air):
        dis = []
        if c in airs:
            for d in [up, down, left, right]:
                if c + d in airs:
                    #dis.append(ssd(visibles[c], visibles[c+d]))
                    dis.append(normalized_ssd(visibles[c], visibles[c+d]))
            ssds[c] = sum(dis) / len(dis)
    return ssds

def mk_openness(is_air, method):
    openness = np.zeros(is_air.shape)
    for c in iter2d(is_air):
        openness[c] = is_air[c] * method(c, is_air)
    return openness

#TODO scipy.ndimage.convolve ?
# Can't use scipy convolve because I want blur to only happen for tiles with the same is_air

def blur(openness):
    blur_array = np.zeros(openness.shape)
    for c in iter2d(openness):
        dis = []
        for d in [Coord(0,0), up, down, left, right]:
            if inbounds(c+d, openness) and copysign(1, openness[c+d]) == copysign(1, openness[c]):
                dis.append(openness[c+d])
        blur_array[c] = sum(dis) / len(dis)
    return blur_array

ClusterState = namedtuple("ClusterState", ["clusters", "neighbors", "pairwise_heap"])

class Cluster(object):
    
    def __init__(self, coords, stats):
        self.coords = coords
        self.stats = stats
        self._mean = self.mean
    
    def merge(self, other):
        assert len(self.coords & other.coords) == 0, "Clusters share a location!"
        return Cluster(self.coords | other.coords, self.stats + other.stats)

    @property
    def mean(self):
        return sum(self.stats) / len(self.stats)
    
    def mean_d(self, other):
        return abs(self._mean - other._mean)
    
    def euc_mean(self, other):
        return (self._mean - other._mean)**2
    
    def var_d(self, other):
        v1 = np.std(self.stats)**2 + np.std(other.stats)**2
        v2 = np.std(self.stats + other.stats)**2
        return v2-v1
    
    def d(self, other):
        return self.euc_mean(other)
    
# Just duck-type - requires merge(.) and d(.) methods
class VisibilityCluster(object):
    
    def __init__(self, coords, visibles):
        self.coords = coords
        self.visibles = visibles
        
    def merge(self, other):
        assert len(self.coords & other.coords) == 0, "Clusters share a location!"
        return VisibilityCluster(self.coords | other.coords, self.visibles | other.visibles)
        
    def ssd(self, other):
        return len(self.visibles - other.visibles) + len(other.visibles - self.visibles)
    
    def ssdn(self, other):
        return self.ssd(other) / len(self.visibles | other.visibles)
    
    # This is bad
    def mut_visibility(self, other):
        # Higher is better
        # Ranges from -2 to 0
        return - len(other.visibles & self.coords) / len(self.coords) - len(self.visibles & other.coords) / len(other.coords)
    
    # This is bad
    # Kind of like average openness, but doesn't double count
    def openness(self, other):
        return abs((len(self.visibles) / len(self.coords)) - (len(other.visibles) / len(other.coords)))
    
    def d(self, other):
        #return self.ssd(other)
        return self.ssdn(other)
        #return self.mut_visibility(other)
        #return self.openness(other)
    
# Determine a canonical name for each cluster
def canon(c1, c2):
    if c2 < c1:
        return (c2, c1)
    else:
        return (c1, c2)

def merge(c1, c2, cluster_state):
    clusters, neighbors, pairwise_heap = cluster_state
    #print(neighbors[c1], neighbors[c2])
    #na = neighbors[c1]
    #nb = neighbors[c2]
    #nc = na | nb
    #nc.remove(c1)
    #nc.remove(c2)
    # Merge the two clusters and clean up data for clusters and pairwise_dict
    c3 = clusters[c1].merge(clusters[c2])
    #TODO: keep nested tags and just remove heap entries?
    #TODO: this way you could recover the hierarchy tree, rather than just the clusters
    # Arbitrarily keep c1 as the merged cluster and drop c2
    clusters[c1] = c3
    del clusters[c2]
    # c1 is adjacent to exactly the adjacencies of both old clusters
    neighbors[c1] |= neighbors[c2]
    # Fix up pairwise distances
    # First, we need to clean up adjacencies involving c2
    for n in neighbors[c2]:
        if n != c1:
            del pairwise_heap[canon(c2, n)]
            # Fix up neighbors
            neighbors[n].remove(c2)
            neighbors[n].add(c1)
    del neighbors[c2]
    # c2 was a neighbor of c1, but c2 is gone
    neighbors[c1].remove(c2)
    # c1 was a neighbor of c2, but shouldn't be a neighbor of itself
    neighbors[c1].remove(c1)
    # Next, add new adjacencies to c1
    for n in neighbors[c1]:
        d = clusters[c1].d(clusters[n])
        pairwise_heap[canon(c1, n)] = d
    #assert neighbors[c1] == nc, f"{neighbors[c1]}, {nc}"

def mk_local_pairwise(clusters):
    # We'll use a heap to keep track of the pairwise distances
    pairwise_heap = heapdict({})
    neighbors = defaultdict(set)
    for c1 in clusters:
        for direction in [up, down, left, right]:
            c2 = c1 + direction
            if c2 in clusters:
                neighbors[c1].add(c2)
                d = clusters[c1].d(clusters[c2])
                pairwise_heap[canon(c1, c2)] = d
    return neighbors, pairwise_heap
    
def initial_conditions_open(openness, mask=None):
    # Set up initial conditions
    # Each cell is in its own cluster
    clusters = {}
    for c in iter2d(openness):
        if mask is None or c in mask:
            clusters[c] = Cluster(set([c]), [openness[c]])
    neighbors, pairwise_heap = mk_local_pairwise(clusters)
    return ClusterState(clusters, neighbors, pairwise_heap)

def initial_conditions_visible(visibles, mask=None):
    clusters = {}
    for c in visibles:
        if mask is None or c in mask:
            clusters[c] = VisibilityCluster(set([c]), visibles[c])
    neighbors, pairwise_heap = mk_local_pairwise(clusters)
    return ClusterState(clusters, neighbors, pairwise_heap)

# Agglomerate the clusters!
def glom(cluster_state, threshold):
    n = 0
    (c1, c2), min_d = cluster_state.pairwise_heap.popitem()
    while min_d < threshold and len(cluster_state.pairwise_heap) > 0:
        #print(f"Merging {c1} with {c2} on iteration {n} @ {min_d}")
        merge(c1, c2, cluster_state)
        (c1, c2), min_d = cluster_state.pairwise_heap.popitem()
        n += 1
    #print("Done")
    cluster_state.pairwise_heap[(c1, c2)] = min_d
    return cluster_state

def hierarchical_cluster(openness, threshold, mask=None):
    assert threshold < float("inf")
    #print("Computing pairwise distances")
    cluster_state = initial_conditions_open(openness, mask)
    #print("Clustering")
    # Now cluster!
    return glom(cluster_state, threshold)

# Best-merge clusters of size < threshold until no such clusters exist (or are isolated)
def cluster_cleanup(cluster_state, threshold, randomly=True):
    done = set()
    # Compute this dynamically since it will change during the loop
    while True:
        to_clean = [k for k,v in cluster_state.clusters.items() if len(v.coords) < threshold and k not in done]
        if len(to_clean) == 0:
            return
        if randomly:
            tc = random.choice(to_clean)
        else:
            tc = to_clean[0]
        #print(f"{len(to_clean)} clusters left")
        #print(f"Cleaning {tc} of size {len(cluster_state.clusters[tc].coords)}")
        # Find the nearest neighbor and merge
        if len(cluster_state.neighbors[tc]) > 0:
            nvs = [(c2, cluster_state.pairwise_heap[canon(tc, c2)]) for c2 in cluster_state.neighbors[tc]]
            if randomly:
                random.shuffle(nvs)
            best_merge, _ = min(nvs, key = lambda x: x[1])
            merge(tc, best_merge, cluster_state)
        # The cluster is too small, but doesn't have an appropriate neighbor
        else:
            done.add(tc)

#TODO: adaptive hierarchical clustering
# Where a pair of nodes is removed from pairwise_heap if the distance is larger than the average structure size (see below)
# the "average structure size" is computed from the structure size within each cluster
# AND clustering continues even when a pair are deemed incompatible
# and only stops when ALL pairs are incampatible -- pairwise_heap is empty
# This allows the clustering condition to adapt to local structure within the clusters
# without relying on features of the global statistics
# For example, using global average structure size wouldn't work for a castle in a large field
# -> castle would be forced to become one structure for a sufficiently large field.

#TODO: if the boundary region is 1 standard deviation away from the mean of either cluster it belongs to, then don't merge
# This doesn't work in general (because size 1 regions have std 0)
# But lets look at the distribution of (boundary avg - center avg) anyways

sort_mean = lambda c, clusters: clusters[c].mean
sort_vis = lambda c, clusters: len(clusters[c].visibles)
sort_random = lambda c, clusters: random.random()

def mk_class_array(openness, cluster_state, sort=None):
    clusters = cluster_state.clusters
    class_array = np.zeros(openness.shape)
    if sort is not None:
        kf = lambda c: sort(c, clusters)
        sc = sorted(clusters.keys(), key=kf)
    else:
        sc = clusters.keys()
    classes = {label: c for label, c in zip(sc, range(len(clusters.keys())))}
    for label, cluster in clusters.items():
        for c in cluster.coords:
            class_array[c] = classes[label] + 1
    return class_array

#TODO: I have very little understanding of this, but it seems to work pretty well
def cluster_threshold_structure(openness):
    opens = []
    for c in iter2d(openness):
        opens.append(openness[c])
    plus_opens = [o for o in opens if o >= 0]
    # Arbitrary parameter but at least scales to the resolution of openness
    nbins = (int((max(plus_opens) + 1)))
    hist, bin_edges = np.histogram(plus_opens, bins=nbins)
    m = np.median(hist)
    # Find the point where the histogram first touches the median openness
    i = 0
    while hist[i] < m:
        i += 1
    return bin_edges[i-1]

# Find the first distance value of zero
# TODO: this can go very wrong
def cluster_threshold_distance(openness):
    _, _, pairwise_dist = compute_initial_conditions(openness)
    m = int(max(pairwise_dist.values()) + 1)
    hist, bin_edges = np.histogram(list(pairwise_dist.values()), bins=m)
    i=0
    while hist[i] > 0:
        i += 1
    return bin_edges[i]

#TODO: boundary standard deviation distance

def cluster_level(level_array, method, threshold=None):
    is_air = mk_is_air(level_array)
    openness = mk_openness(is_air, method)
    op2 = blur(openness)
    if threshold is None:
        #threshold = cluster_threshold_distance(openness)
        threshold = cluster_threshold_structure(openness)
    cs, ps = hierarchical_cluster(op2, threshold)
    return mk_class_array(op2, cs)
