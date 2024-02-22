from sm_rando.data_types.item_set import ItemSet
from sm_rando.world_rando.rules import AbstractTile

class ConstraintPattern(object):

    def __init__(self, ab_items, ba_items, pattern, adj_tiles, a_tiles, b_tiles, plms, target_a, target_b):
        # What items the pattern constrains, as a MinSetSet
        # ab_items is items required to go from A to B
        # ba_items is items required to go from B to A
        # If items is None, travel is impossible.
        self.ab_items = ab_items
        self.ba_items = ba_items
        # The visual part of the pattern as a LevelState
        self.pattern = pattern
        # The region which has to be inside the adjacency between A and B
        self.adj_tiles = adj_tiles
        # The region that must be within subroom A
        self.a_tiles = a_tiles
        # The region that must be within subroom B
        self.b_tiles = b_tiles
        # What post-load modifications (if any) to add to the room in order to enforce
        # the constraint
        self.plms = plms
        # Motion targets. When constructing an (A,B) -> (B,C) edge inside room B, search from
        # (A,B).target_b to (B,C).target_c
        #TODO: allow multiple targets
        self.target_a = target_a
        self.target_b = target_b
        # Determine the position of
        self.adj_bbox = bounding_box(self.adj_tiles)
        self.adj_rel_pos = self.adj_bbox.start

    def find_placements(self, subroom_a_tiles, subroom_b_tiles, adj_tiles, abstract_level):
        placements = []
        #TODO: slide the bounding box of the self.adj_tiles over the bounding box of adj_tiles
        r = bounding_box(adj_tiles)
        adj_bbox_vec = self.adj_rel_pos.size_coord()
        r_vec = r.size_coord()
        # If the desired adj doesn't fit on the given adj
        if r_vec.x < adj_bbox_vec.x or r_vec.y < adj_bbox_vec.y:
            return []
        possible_placements = Rect(r.start, r.end-adj_bbox_vec)
        # Possible placements for the entire pattern are relative to the possible placements for the adjacency
        for pos in possible_placements.translate(-self.adj_rel_pos):
            # Check that the placement respects constraints
            rel_a_tiles = set_translate(self.a_tiles, pos)
            if not rel_a_tiles <= subroom_a_tiles:
                continue
            rel_b_tiles = set_translate(self.b_tiles, pos)
            if not rel_b_tiles <= subroom_b_tiles:
                continue
            rel_adj_tiles = set_translate(self.adj_tiles, pos)
            if not rel_adj_tiles <= adj_tiles:
                continue
            # Now ensure that the pattern fits
            if check_pattern(abstract_level, self.pattern, pos):
                placements.append(pos)
        return placements

    def apply(self, placement, room, node_a, node_b, graph):
        # Place the pattern at the given position
        mk_pattern(room.abstract_level, self.pattern, placement)
        # Make the required changes to the graph
        graph.add_edge(node_a, node_b, self.ab_items)
        graph.add_edge(node_b, node_a, self.ba_items)

#TODO: subclass
class DoorConstraintPattern(object):

    def __init__(self, ab_items, ba_items, a_pattern, b_pattern, a_adj_tiles, b_adj_tiles,
            a_tiles, b_tiles, a_plms, b_plms, target_a, target_b):
        self.pattern_ab = ConstraintPattern(ab_items, ItemSet(), a_pattern,
                a_adj_tiles, a_tiles, set([]), a_plms, target_a, None)
        self.pattern_ba = ConstraintPattern(ba_items, ItemSet(), b_pattern,
                b_adj_tiles, b_tiles, set([]), b_plms, target_b, None)
        #TODO: when *placing* a door, require that the abstract tiles have a corresponding PLM
        # When replacing Missile Door tiles for placing a door, check that a Missile Door Cap PLM exists

    def find_placements(self, subroom_a_tiles, subroom_b_tiles, door_a, door_b, abstract_a, abstract_b):
        a_placements = self.pattern_ab.find_placements(subroom_a_tiles, set([]), door_a.obstacle_set, abstract_a)
        b_placements = self.pattern_ba.find_placements(subroom_b_tiles, set([]), door_b.obstacle_set, abstract_b)
        #TODO: check for placement pairs that are compatible with each other!
        return a_placements, b_placements

    def apply(self, placement, room_a, room_b, node_a, node_b, graph):
        placement_a, placement_b = placement
        self.pattern_ab.apply(placement_a, room_a, node_a, node_b, graph)
        # Must reverse the nodes since ba represents b->a
        self.pattern_ba.apply(placement_b, room_b, node_b, node_a, graph)

def check_pattern(level, pattern, pos):
    for p in pattern:
        rel_p = pos + p
        l = level[rel_p]
        if l != AbstractTile.UNKNOWN:
            if l != pattern[p]:
                return False
    return True

def mk_pattern(level, pattern, pos):
    for p in pattern:
        rel_p = pos + p
        if level[rel_p] == AbstractTile.UNKNOWN:
            level[rel_p] = pattern[p]
        else:
            assert level[rel_p] == pattern[p]

defaults = {
    # Items required to cross A<->B
    # Can also have A->B or B->A separately
    "A<->B": "",
    # Definition of samus state for a_target (position from image)
    "a_pose": "Stand",
    "a_vv": "0",
    "a_vv": "Run,0",
    # Definition of samus state for b_target
    "b_pose": "Stand",
    "b_vv": "0",
    "b_vh": "Run,0",
    # PLM definitions
    "plms": ""
    }
# A "Door" constraint will have a door flag and two plm definitions

def parse_constraint_patterns(pattern_file):
    pass

def enforce_constraints(planning_graph, item_order, constraint_patterns):
    # Create the constraint pattern dictionary Item -> ConstraintPattern
    # by dropping patterns that are not consistent with the item order
    # For example, if pattern A constrains {S, MB} and MB < S, pattern A
    # appears in d[S] but not in d[MB]
    # In general, a MinSetSet constrains only the smallest (over all itemsets) largest (over the chosen itemset) item
    # ...
    for item in item_order[::-1]:
        # Determine the cuttable edges for that item by checking the applicable constraint patterns
        cuttable_edges = set([...])
        # Create a corresponding edge weights table
        edge_weights = {(a, b): w for a,b in permutations(nodes, nodes)
        # Use network flow to find a cut that 
        pass

def set_translate(s, pos):
    return set([t + pos for t in s])
