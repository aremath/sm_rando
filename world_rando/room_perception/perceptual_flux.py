from itertools import combinations
from functools import reduce
import math
from tqdm.auto import tqdm
from heapdict import heapdict
from matplotlib.pyplot import scatter, matshow, gca
from matplotlib.collections import LineCollection

from world_rando.room_perception.angleset import *
from world_rando.room_perception.isovision import *
from world_rando.room_perception.geometry import *
from world_rando.coord import *

# Finding the surfaces from a solid / 

# Find the boundaries for each direction (some cells may have multiple boundaries)
def mk_boundaries(is_air, include_bounds=True):
    boundaries = {}
    for d in cardinal_ds:
        boundaries[d] = set()
        for c in iter2d(is_air):
            if inbounds(c + d, is_air) and is_air[c] == -1 and is_air[c + d] == 1:
                boundaries[d].add(c)
            if include_bounds and is_air[c] == 1 and not inbounds(c + d, is_air):
                boundaries[d].add(c)
    return boundaries

#TODO: consider a smoothing algorithm that makes non-axis-aligned surfaces (e.g. marching squares)
#TODO: make appropriate sloped surfaces for sloped tiles

def mk_boundary_surfaces(is_air):
    surfaces = []
    surfaces.append((Coord(0, 0), Coord(0, is_air.shape[1])))
    surfaces.append((Coord(0, 0), Coord(is_air.shape[0], 0)))
    surfaces.append((Coord(is_air.shape[0], 0), Coord(is_air.shape[0], is_air.shape[1])))
    surfaces.append((Coord(0, is_air.shape[1]), Coord(is_air.shape[0], is_air.shape[1])))
    return surfaces

def mk_lines(is_air):
    surfaces = []
    # subsegs[a] = [b], the subsegments that make up the segment a
    subsegs = {}
    boundaries = mk_boundaries(is_air, True)
    ortho = {up: right, down: right, left: down, right: down}
    add = {up: Coord(0,0), down: Coord(0,1), left: Coord(0,0), right: Coord(1,0)}
    # Find maximal surfaces
    for c in iter2d(is_air):
        for d in cardinal_ds:
            o = ortho[d]
            if c in boundaries[d]:
                #print(c)
                these_subsegs = []
                extend = c
                while inbounds(extend, is_air) and extend in boundaries[d]:
                    boundaries[d].remove(extend)
                    seg = (extend + add[d], extend + add[d] + o)
                    these_subsegs.append(seg)
                    extend = extend + o
                segment = (c + add[d], extend + add[d])
                surfaces.append(segment)
                subsegs[segment] = these_subsegs
    # Add surfaces that cover the boundaries
    #surfaces.extend(mk_boundary_surfaces(is_air))
    return surfaces, subsegs

def mk_tiles(is_air):
    surfaces = []
    boundaries = mk_boundaries(is_air)
    ortho = {up: right, down: right, left: down, right: down}
    add = {up: Coord(0,0), down: Coord(0,1), left: Coord(0,0), right: Coord(1,0)}
    for d in boundaries:
        for t in boundaries[d]:
            segment = (t + add[d], t + add[d] + ortho[d])
            surfaces.append(segment)
    return surfaces

def mk_perception(point, surfaces):
    """For each surface in surfaces, compute the set of angles that collide with that surface first, starting at point"""
    ordered_surfaces = sorted(surfaces, key=lambda x: segment_fraction(x, 0.5).euclidean(point))
    #print(len(ordered_surfaces))
    fully_occluded = set()
    perception = {}
    # Generate initial perceptions (without occlusion)
    for surface in ordered_surfaces:
        perception[surface] = line_segment_interval(point, surface)
    # Occlude the surfaces
    for surface in ordered_surfaces:
        # Occluded surfaces do not need to be processed since any surface which is (partially) occluded by a fully occluded surfaces is
        # at least as occluded by the surfaces that occlude the surface which would occlude it (yes)
        if surface in fully_occluded:
            continue
        for surface2 in ordered_surfaces:
            if surface2 in fully_occluded:
                continue
            # Surface may occlude surface2
            #print(surface, surface2)
            visible = occlude(point, surface2, surface)
            #print(perception[surface2], visible)
            perception[surface2] = perception[surface2] & visible
            assert perception[surface2] is not None
            if perception[surface2].size == 0:
                fully_occluded.add(surface2)
                pass
    return perception, fully_occluded

# Convert back from the perceived angles to the segment

def interval_points(point, segment, interval):
    """Return the subsegment corresponding to a given interval"""
    p1 = angle_intersect(point, interval.start, segment)
    p2 = angle_intersect(point, interval.end, segment)
    # The endpoints of the visible part of a segment should be on the segment
    assert p1 is not None
    assert p2 is not None
    return (p1, p2)

def set_points(point, segment, set):
    """Returns all subsegments corresponding to a set of intervals"""
    if set.pure:
        return [interval_points(point, segment, set)]
    else:
        return [interval_points(point, segment, i) for i in set.intervals]

def triangularize(point, perception):
    """Return the set of triangles that constitute a perception"""
    points = [point]
    triangles = []
    for k,v in perception.items():
        #print(v)
        sp = set_points(point, k, v)
        #print(sp, len(sp))
        for pair in sp:
            #print("pair:", pair)
            p1, p2 = pair
            i1 = len(points)
            points.append(p1)
            i2 = i1 + 1
            points.append(p2)
            # Will this be anticlockwise??
            #print(p1, p2)
            triangles.append((0, i1, i2))
    x = np.array([p.x for p in points])
    y = np.array([p.y for p in points])
    t = np.array(triangles)
    return x, y, t

# Converting from perceptions to probability distributions
def mk_perception_good(point, perception, subsegments):
    good_perception = {}
    for surface, visible_set in perception.items():
        for sub in subsegments[surface]:
            good_perception[sub] = line_segment_interval(point, sub) & visible_set
    return good_perception

def mk_surface_probs(perception):
    return {k: (v.size / twopi) for k,v in perception.items()}

def surface_entropy(probs):
    entropy = 0
    for k,v in probs.items():
        if v != 0:
            entropy -= v * math.log(v, 2)
    return entropy

def prob_add(prob, prob_add, weight=1):
    for k,v in prob_add.items():
        if k in prob:
            prob[k] = prob[k] + (v * weight)
        else:
            prob[k] = (v * weight)

def mk_mixture(probs, weights=None):
    mixture = {}
    if weights is None:
        weights = [1] * len(probs)
    for i, p in enumerate(probs):
        prob_add(mixture, p, weights[i])
    return {k : v / sum(weights) for k,v in mixture.items()}

# JSD assuming the variable X is "which surface was hit by the ray"
def surface_prob_jsd(prob_a, prob_b):
    mixture = mk_mixture([prob_a, prob_b])
    h_m = surface_entropy(mixture)
    h_a = surface_entropy(prob_a)
    h_b = surface_entropy(prob_b)
    return h_m - 0.5 * (h_a + h_b)

def perception_surface_distance(perception_a, perception_b):
    prob_a = mk_surface_probs(perception_a)
    prob_b = mk_surface_probs(perception_b)
    return surface_prob_jsd(prob_a, prob_b)

def mk_all_surface_probs(is_air, surfaces, subsegments, good=True):
    """Compute the surface probability distributions for each center of each air tile in is_air"""
    surface_probs = {}
    for c in tqdm(iter2d(is_air), total = is_air.shape[0] * is_air.shape[1]):
        if is_air[c] == 1:
            cc = c + Coord(0.5, 0.5)
            p, _ = mk_perception(cc, surfaces)
            if good:
                surface_probs[c] = mk_surface_probs(mk_perception_good(cc, p, subsegments))
            else:
                surface_probs[c] = mk_surface_probs(p)
    return surface_probs

def mk_neighbor_infos(is_air, surface_probs):
    """Use the surface probabilities to compute the JSD (mutual information) between neighboring cells"""
    infos = np.zeros_like(is_air)
    for c in iter2d(infos):
        if is_air[c] == 1:
            p_a = surface_probs[c]
            jsds = []
            for d in cardinal_ds:
                #c2 = c + (d.scale(2))
                c2 = c + d
                if inbounds(c2, is_air) and is_air[c2] == 1:
                    p_b = surface_probs[c2]
                    jsds.append(surface_prob_jsd(p_a, p_b))
            if len(jsds) > 0:
                infos[c] = sum(jsds) / len(jsds)
                #infos[c] = max(jsds)
    return infos

def mk_distance(is_air):
    """Compute the Manhattan distance from each cell to the nearest wall"""
    distance = np.zeros_like(is_air)
    for c in iter2d(is_air):
        if is_air[c] == -1:
            distance[c] = 0
        else:
            distance[c] = -1
    changed = True
    while changed:
        distance_k = np.zeros_like(is_air)
        changed = False
        for c in iter2d(is_air):
            m = None
            if distance[c] == -1:
                for d in cardinal_ds:
                    c2 = c + d
                    if inbounds(c2, is_air) and distance[c2] != -1:
                        if m is None:
                            m = distance[c2] + 1
                        else:
                            m = min(m, distance[c2] + 1)
                if m is not None:
                    changed = True
                    distance_k[c] = m + 1 # +1 to cancel the -1
        distance = distance + distance_k
    return distance

def mk_minima(infos, is_air):
    """Find the local minima of infos"""
    minima = []
    for c in iter2d(infos):
        if is_air[c] == 1:
            is_min = True
            for d in cardinal_ds:
                c2 = c + d
                if inbounds(c2, infos) and is_air[c2] == 1 and infos[c2] < infos[c]:
                #if inbounds(c2, infos) and is_air[c2] == 1 and infos[c2] < infos[c] + 0.001:
                    is_min = False
            if is_min:
                minima.append(c)
    return minima

# Agglomerative clustering for the minima

# Threshold ~= 0.6 seems to work well in practice
def agglomerate(minima, surface_probs, threshold):
    cluster_mixes = {frozenset([c]): surface_probs[c] for c in minima}
    cluster_ds = heapdict({})
    for (c1, c2) in combinations(minima, 2):
        c1s = frozenset([c1])
        c2s = frozenset([c2])
        cluster_ds[(c1s, c2s)] = surface_prob_jsd(cluster_mixes[c1s], cluster_mixes[c2s])
    (c1, c2), min_d = cluster_ds.popitem()
    n = 0
    while min_d < threshold and len(cluster_ds) > 0:
        merge = c1 | c2
        merge_mix = mk_mixture([cluster_mixes[c1], cluster_mixes[c2]], [len(c1), len(c2)])
        del cluster_mixes[c1]
        del cluster_mixes[c2]
        for c in cluster_mixes:
            cluster_ds[(c, merge)] = surface_prob_jsd(cluster_mixes[c], merge_mix)
        cluster_mixes[merge] = merge_mix
        #print(n)
        n+=1
        while True:
            (c1, c2), min_d = cluster_ds.popitem()
            if c1 in cluster_mixes and c2 in cluster_mixes:
                break
    return cluster_mixes

offset = Coord(-0.5, -0.5)

def drawc(coord):
    c2 = coord + offset
    scatter(c2.x, c2.y)

def draw_segs(segments, color="royalblue", offset = offset):
    surfaces = [(s + offset, t + offset) for (s,t) in segments]
    lc = LineCollection(surfaces, linewidths = 2, color=color)
    ax = gca()
    ax.add_collection(lc)

def draw_cluster(glom, segs=True):
    for cluster in glom:
        xs = [c.x for c in cluster]
        ys = [c.y for c in cluster]
        scatter(xs, ys)
        ac = Coord(sum(xs) / len(xs), sum(ys) / len(ys))
        if segs:
            segs = [(ac, c) for c in cluster]
            draw_segs(segs, offset = Coord(0,0))

# Packaging functions

def compute_surfaces(is_air, good=True):
    surfaces, subsegs = mk_lines(is_air)
    surface_probs = mk_all_surface_probs(is_air, surfaces, subsegs, good)
    infos = mk_neighbor_infos(is_air, surface_probs)
    return surface_probs, infos

def compute_room_surfaces(room_name, objnames, good=True):
    room_state = objnames[room_name].state_chooser.default
    room_array = objnames[room_name].state_chooser.default.level_data.level_array.layer1
    is_air = mk_is_air(room_array)
    surfaces, subsegs = mk_lines(is_air)
    #surfaces = mk_tiles(is_air)
    surface_probs = mk_all_surface_probs(is_air, surfaces, subsegs, good)
    infos = mk_neighbor_infos(is_air, surface_probs)
    return is_air, surface_probs, infos

def show_clusters(is_air, surface_probs, infos, draw=True, threshold=0.6, segs=True):
    minima = mk_minima(infos, is_air)
    glom = agglomerate(minima, surface_probs, threshold)
    matshow(infos.T)
    if draw:
        draw_cluster(glom, segs)
    return glom
