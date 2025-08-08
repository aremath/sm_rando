from functools import cache

from bdds.node_bdds import *
import omega
omega.logic.bitvector.ALU_BITWIDTH=42
from encoding.parse_rooms import parse_rooms, parse_exits, dictify_rooms

major_items = ["MB", "B", "SPB", "G", "SA", "V", "GS", "SB", "HJ", "CB", "WB", "PLB", "Spazer", "XR", "IB", "SJ"]
minor_items = ["M", "S", "PB", "E", "RT"]
rando_items = ["B", "MB", "PB", "SPB", "S", "M", "G", "SA", "V", "GS", "SB", "HJ", "CB", "WB", "E", "PLB", "Spazer", "RT", "XR", "IB", "SJ"]
assert set(rando_items) == set(major_items) | set(minor_items)

# Closure stuff
def find_closure_sbfs(context, trans, start_bdd):
    n = 0
    closure = start_bdd & trans
    closure_last = context.false
    trans_tn = context.let(prev_to_temp, trans)
    while closure != closure_last:
        closure_last = closure
        closure |= context.exist(temps, context.let(next_to_temp, closure) & trans_tn)
        print(n, closure.dag_size)
        n += 1
    return closure

def find_reachable_sbfs(context, trans, start_bdd):
    n = 0
    reachable = start_bdd
    reachable_last = context.false
    while reachable != reachable_last:
        reachable_last = reachable
        reachable |= context.let(next_to_prev, context.exist(prevs, reachable & trans))
        print(n, reachable.dag_size)
        n += 1
    return reachable

# Find items that do not affect reachability:
bad_items = [
    # 'Implied' items
    "Botwoon",
    "Spore_Spawn",
    "Golden_Torizo",
    "Drain",
    "Shaktool",
    # Items that don't impact reachability
    "Spazer",
    "XR",
    "RT",
    "Ceres_Ridley",
]
nuisances = [f"{i}_prev" for i in bad_items] + [f"{i}_next" for i in bad_items]

#TODO: minor items
def show_design(pick):
    for v,id in pick.items():
        print(f"{v}: {major_items[id]}")

n_major_rando = 16
n_minor_rando = 0

def get_majors(design):
    major_nodes = []
    minor_nodes = []
    other_nodes = []
    for room_name, room in design["Rooms"].items():
        for node_name, d in room["Drops"].items():
            node_str = room_name + "_" + node_name
            if d in major_items:
                major_nodes.append(node_str)
            elif d in minor_items:
                minor_nodes.append(node_str)
            else:
                other_nodes.append(node_str)
    assert len(major_nodes) == len(major_items)
    assert len(minor_nodes) == 100 - len(major_nodes)
    return major_nodes, minor_nodes, other_nodes

def add_drop_vars(context, major_drop_nodes, minor_drop_nodes):
    design_vars = {
        **{ f"major_drop_{node}": (0,len(major_items)-1) for node in major_drop_nodes },
        **{ f"minor_drop_{node}": (0,len(minor_items)-1) for node in minor_drop_nodes }
    }
    if len(design_vars) > 0:
        context.declare(**design_vars)
    return design_vars

def add_one_hot_vars(context, important_nodes):
    # The one-hot vars
    node_vars_prev = { f"at_{i}_prev" : (0,1) for i in important_nodes }
    node_vars_next = { f"at_{i}_next" : (0,1) for i in important_nodes }
    context.declare(**node_vars_prev)
    context.declare(**node_vars_next)
    return

# Mess with the order
def static_order_score(name):
    var,tense,bit = name.rsplit('_', 2)
    bit = int(bit)
    is_design = var.startswith("major") or var.startswith("minor")
    is_loc = var.startswith("node_id")
    is_at = var.startswith("at")
    return (is_design, not is_loc, not is_at, var, -bit, tense)

def mk_binary_to_one_hot(context, important_nodes, node_ids):
    binary_to_one_hot = context.true
    uniqueness = context.add_expr(" + ".join([f"at_{node}_prev" for node in important_nodes] + ["0"]) + " = 1")
    uniqueness &= context.add_expr(" + ".join([f"at_{node}_next" for node in important_nodes] + ["0"]) + " = 1")
    #uniqueness = context.true
    for i in important_nodes:
        nid = node_ids[i]
        binary_to_one_hot &= context.add_expr(f"node_id_prev = {nid} <-> at_{i}_prev = 1")
        binary_to_one_hot &= context.add_expr(f"node_id_next = {nid} <-> at_{i}_next = 1")
    return binary_to_one_hot & uniqueness

def mk_valid(context, major_drop_nodes, minor_drop_nodes):
    # Ensure uniqueness and validity
    validity = context.true
    for node in major_drop_nodes:
        validity &= context.add_expr(f"major_drop_{node} < {len(major_items)}")
    for node in minor_drop_nodes:
        validity &= context.add_expr(f"minor_drop_{node} < {len(major_items)}")

    # Only drop one thing
    # Sum is faster to compute than O(n^2) !=s
    uniqueness = context.true
    for i,item in enumerate(major_items):
        uniqueness &= context.add_expr(" + ".join([f"ite(major_drop_{node} = {i},1,0)" for node in major_drop_nodes] + ["0"]) + " <= 1")

    valid_design = validity & uniqueness
    return valid_design

def mk_edits(design, major_drop_nodes, minor_drop_nodes):
    edits = []
    for room_name, room in design["Rooms"].items():
        for node_name, d in room["Drops"].items():
            name = room_name + "_" + node_name
            if d in major_items:
                if name in major_drop_nodes:
                    edits.append(f"ite(major_drop_{name} = {major_items.index(d)},0,1)")
            if d in minor_items:
                if name in minor_drop_nodes:
                    edits.append(f"ite(minor_drop_{name} = {minor_items.index(d)},0,1)")
    all_edits = " + ".join(edits)
    return all_edits

def mk_majors_unchanged(context, design):
    major_items_unchanged = context.true
    bosses = design["Bosses"]
    for i in major_items + list(bosses.keys()):
        major_items_unchanged &= context.add_expr(f"{i}_prev = {i}_next")
    return major_items_unchanged

#TODO: inherit from node_bdds / NodeEnv
#TODO: rename to DesignEnv or NodeDesignEnv
class DesignInfo(object):

    def __init__(self, rooms_path, exits_path, trans_important_path, load_important=True):
        if not load_important:
            assert trans_important_path is None
        self.rooms = parse_rooms(rooms_path)
        self.exits = parse_exits(exits_path)
        self.design = dictify_rooms(self.rooms, self.exits)
        self.node_ids = mk_node_ids(self.rooms, rename=True)
        self.node_ids_rev = {i:n for n,i in self.node_ids.items()}
        self.context = mk_context_id(self.node_ids)
        major, minor, other = get_majors(self.design)
        self.major_drop_nodes = major[:n_major_rando]
        self.minor_drop_nodes = minor[:n_minor_rando]
        # Add design vars
        self.design_vars = add_drop_vars(self.context, self.major_drop_nodes, self.minor_drop_nodes)
        # One-hot stuff
        self.important_nodes = major + other + ["Landing_Site_Ship", "Landing_Site_End"]
        # Can reverse-engineer important nodes from trans_important
        #item_vars = prevs[1:]
        #nodes = self.context.exist(item_vars + nexts, self.trans_important)
        #self.important_nodes = [self.node_ids_rev[i["node_id_prev"]] for i in self.context.pick_iter(nodes)]
        add_one_hot_vars(self.context, self.important_nodes)
        # Reorder whether or not we are building important
        self.context.bdd.reorder({v:i for i,v in enumerate(sorted(self.context.bdd.vars, key=static_order_score))})
        self.binary_to_one_hot = mk_binary_to_one_hot(self.context, self.important_nodes, self.node_ids)
        self.valid_design = mk_valid(self.context, self.major_drop_nodes, self.minor_drop_nodes)
        self.edits = mk_edits(self.design, self.major_drop_nodes, self.minor_drop_nodes)
        self.trans = self.mk_trans()
        self.trans = self.context.exist(nuisances, self.trans)
        majors_unchanged = mk_majors_unchanged(self.context, self.design)
        self.trans_item = self.trans & ~majors_unchanged
        self.trans_nav = self.trans & majors_unchanged
        # Make sure that trans_nav is not design-conditioned
        assert not set(self.design_vars.keys()) & set(self.context.support(self.trans_nav))
        if load_important:
            self.trans_important = self.context.bdd.load(trans_important_path)[0]
        else:
            important_prev = self.reduce_or([self.context.add_expr(f"node_id_prev = {node_ids[waypoint]}") for waypoint in important_nodes])
            self.trans_important = find_closure_sbfs(self.context, self.trans_nav, important_prev) & self.context.let(prev_to_next, important_prev)
        self.teleport_trans = self.trans_item | self.trans_important


    def reduce_and(self, clauses):
        return reduce(lambda x, y: x & y, clauses, self.context.true)

    def reduce_or(self, clauses):
        return reduce(lambda x, y: x | y, clauses, self.context.false)

    def loc_id(self, room_name, node_name, when="prev"):
        node_id = self.node_ids[f"{room_name}_{node_name}"]
        return self.context.add_expr(f"node_id_{when} = {node_id}")

    @cache
    def item_transitions(self, item_gained=None):
        if item_gained is None:
            return self.context.add_expr("(items_unchanged)", with_ops = True)
        clauses = []
        for i in self.design["Items"] | self.design["Bosses"]:
            if i == item_gained:
                clause = self.context.add_expr(f"{i}_prev < {i}_next")
            else:
                clause = self.context.add_expr(f"{i}_prev = {i}_next")
            clauses.append(clause)
        return self.reduce_and(clauses)

    def itemset_to_bdd(self, itemset):
        if len(itemset) == 0:
            return self.context.true
        else:
            return self.reduce_and([self.context.add_expr(f"{item}_prev = 1") for item in itemset])

    def required_itemsets(self, itemsets):
        return self.reduce_or([self.itemset_to_bdd(itemset) for itemset in itemsets])

    def rando_transitions(self, room_name, node_name, family, possible_items):
        t = self.context.false
        node_name = room_name + "_" + node_name
        drop_name = f"{family}_drop_{node_name}"
        for i,item in enumerate(possible_items):
            t |= self.context.add_expr(f"{drop_name} = {i}") & self.item_transitions(item)
        return t

    def mk_edit_distance(self, distance, mode="<="):
        return self.context.add_expr(self.edits + f" {mode} {distance}")

    def mk_trans(self):
        # Build individual BDDs
        room_bdds = []
        door_bdds = []
        for room_name, room in self.design['Rooms'].items():
            links = []
            for node_name in room['Nodes']:
                s = self.loc_id(room_name, node_name) & self.loc_id(room_name, node_name, when="next") & self.item_transitions()
                links.append(s)
                if node_name in room['Drops']:
                    if room_name + "_" + node_name in self.major_drop_nodes:
                        s = self.loc_id(room_name, node_name) & self.loc_id(room_name, node_name, when="next") & self.rando_transitions(room_name, node_name, "major", major_items)
                    elif room_name + "_" + node_name in self.minor_drop_nodes:
                        s = self.loc_id(room_name, node_name) & self.loc_id(room_name, node_name, when="next") & self.rando_transitions(room_name, node_name, "minor", minor_items)
                    else:
                        s = self.loc_id(room_name, node_name) & self.loc_id(room_name, node_name, when="next") & self.item_transitions(room['Drops'][node_name])
                    links.append(s)
            for node_name, door in room['Doors'].items():
                d = self.loc_id(room_name, node_name) & self.loc_id(door['Room'], door['Node'], when="next") & self.item_transitions()
                door_bdds.append(d)
            for node_name, edges in room['Edges'].items():
                for edge in edges:
                    other_node_name = edge['Terminal']
                    s = self.loc_id(room_name, node_name) & self.loc_id(room_name, other_node_name, when="next") & self.required_itemsets(edge['Requirements']) & self.item_transitions()
                    links.append(s)
            room_bdd = self.reduce_or(links)
            #print(room_bdd.count())
            room_bdds.append(room_bdd)
        doors_bdd = self.reduce_or(door_bdds)
        rooms_bdd = self.reduce_or(room_bdds)
        trans = doors_bdd | rooms_bdd
        return trans

    def mk_itemset_expr(self, itemset, when="prev"):
        clauses = []
        for i in item_mapping:
            if i in itemset:
                clause = self.context.add_expr(f"{i}_{when} = 1")
            else:
                clause = self.context.add_expr(f"{i}_{when} = 0")
            clauses.append(clause)
        return self.reduce_and(clauses)
