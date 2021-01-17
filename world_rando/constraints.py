
class ConstraintPattern(object):

    def __init__(self, items, pattern, adj_interior, adj_region, is_reflexive, spatial_relate, plms):
        # What items the pattern constrains, as a MinSetSet
        self.items = items
        # The visual part of the pattern as a LevelState
        self.pattern = pattern
        # The rectangular region which has to be inside the adjacency
        self.adj_interior = adj_interior
        # The actual passable region that the player travels through within the adjacency
        self.adj_region = adj_region
        # Whether placing the pattern on A->B also creates a constraint on B->A
        self.is_reflexive = is_reflexive
        # What spatial relationships for A, B are necessary for placing the pattern
        # to function as a constraint on A->B
        self.spatial_relate = spatial_relate
        # What post-load modifications (if any) to add to the room in order to enforce
        # the constraint
        self.plms = plms
        #TODO: when *placing* a door, require that the abstract tiles have a corresponding PLM
        # When replacing Missile Door tiles for placing a door, check that a Missile Door Cap PLM exists

    def apply(subroom_a, subroom_b, room_a, room_b):
        pass

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

