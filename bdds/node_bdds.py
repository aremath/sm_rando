from omega.symbolic.fol import Context as OmegaContext

from bdds.bdd_core import *
from abstraction_validation.sm_paths import *
from abstraction_validation.abstractify import abstractify_state, abstractify_boss_info
from encoding.parse_rooms import parse_rooms, parse_exits, dictify_rooms
from data_types.constraintgraph import Item, Boss

# CONTEXT STUFF

def static_order_score(name):
  var,tense,bit = name.rsplit('_', 2)
  return (-int(var=="node_id"),-int(bit),var,tense)

# Only encode node_id and items
def mk_context_id(node_ids):
    context = OmegaContext()
    context.declare(
        node_id_prev = (0,len(node_ids)),
        node_id_next = (0,len(node_ids)),
        node_id_goal = (0,len(node_ids)),
        node_id_temp = (0,len(node_ids)),
    )
    # Try to get a favorable variable ordering
    shared_dict = {}
    for i in item_mapping:
        shared_dict[f"{i}_prev"] = (0,1)
        shared_dict[f"{i}_next"] = (0,1)
        shared_dict[f"{i}_goal"] = (0,1)
        shared_dict[f"{i}_temp"] = (0,1)
    context.declare(**shared_dict)
    context.define(mk_items_unchanged())
    context.bdd.configure(reordering=False)
    context.bdd.reorder({v:i for i,v in enumerate(sorted(context.bdd.vars, key=static_order_score))})
    return context

# Need a list to instantiate prevs, nexts, etc. do NOT use default_context_id
default_context_id = mk_context_id([None])

# Have to refine some stuff from bdd_core for the new context
prev_to_temp = mk_replace(default_context_id, "prev", "temp")
next_to_temp = mk_replace(default_context_id, "next", "temp")
goal_to_next = mk_replace(default_context_id, "goal", "next")
goal_to_prev = mk_replace(default_context_id, "goal", "prev")
prev_to_next = mk_replace(default_context_id, "prev", "next")
next_to_prev = mk_replace(default_context_id, "next", "prev")
temps = [k for k in default_context_id.vars.keys() if k.endswith("_temp")]
nexts = [k for k in default_context_id.vars.keys() if k.endswith("_next")]
prevs = [k for k in default_context_id.vars.keys() if k.endswith("_prev")]
goals = [k for k in default_context_id.vars.keys() if k.endswith("_goal")]
pos_vars = ["node_id_prev", "node_id_next"]
item_vars = list(set(prevs + nexts) - set(pos_vars))

def mk_goal_satisfied_id(context):
    # Expression that holds when the goal is satisfied (for all possible goals)
    goal_satisfied = context.true
    for v1, v2 in zip(nexts, goals):
        sat = context.add_expr(f"{v1} = {v2}")
        #print(sat.dag_size)
        #print(goal_satisfied.dag_size)
        goal_satisfied &= sat
    return goal_satisfied

def mk_policy_id2(trans_pn, context, goal_bdd=None):
    n = 0
    if goal_bdd is not None:
        solved_ng = goal_bdd
    else:
        solved_ng = mk_goal_satisfied_id(context)
    policy_png = trans_pn & solved_ng
    policy_last_png = None
    while policy_png != policy_last_png:
        policy_last_png = policy_png
        solved_pg = context.exist(nexts, policy_png)
        solved_ng = context.let(prev_to_next, solved_pg)
        policy_png |= (trans_pn & ~solved_pg) & solved_ng
        print(n)
        n += 1
    return policy_png

#TODO simpler policy construction
def mk_policy_id(trans_pn, context, goal_bdd=None, maxn=None):
    n = 0
    if maxn is None:
        maxn = float("inf")
    # prev, next, goal
    policy_png = context.false
    covered_ng = mk_goal_satisfied_id(context)
    if goal_bdd:
        covered_ng &= goal_bdd
        #TODO covered_ng = goal_bdd
    covered_last_ng = context.false
    while covered_ng != covered_last_ng and n < maxn:
        # States with edges into a covered state
        covered_last_ng = covered_ng
        covered_pg = context.let(next_to_prev, covered_ng)
        fringe_png = trans_pn & covered_ng & ~covered_pg
        # TODO: consider gluing the fringes together later?
        policy_png |= fringe_png
        #print(fringe_png.count())
        #print(context.exist(nonidns, fringe_png).count())
        #print(list(context.pick_iter(context.exist(nonidns, fringe_png))))
        # Update covered to include the prevs of fringe
        covered_ng |= context.let(prev_to_next, context.exist(nexts, fringe_png))
        print(n, fringe_png.dag_size, covered_ng.dag_size, policy_png.dag_size)
        n += 1
    return policy_png

def get_reachable_id(trans_norule, context, start_bdd):
    n = 0
    covered_p = start_bdd
    covered_last_p = context.false
    while covered_p != covered_last_p:
        covered_last_p = covered_p
        fringe_n = context.exist(prevs, covered_p & trans_norule)
        covered_p |= context.let(next_to_prev, fringe_n)
        print(n, covered_p.dag_size)
        n+=1
    return covered_p

#TODO rename
def determinize2(policy, context):
    policy_det = policy & ~context.exist(temps, policy & context.let(next_to_temp,policy) & context.add_expr("node_id_temp < node_id_next"))
    return policy_det

def get_steps_id(policy, task_bdd, context):
    steps = context.false
    state_p = context.exist(goals, task_bdd)
    goal_g = context.exist(prevs, task_bdd)
    controller_pn = context.exist(goals, policy & goal_g)
    goal_p = context.let(goal_to_prev, goal_g)
    while state_p & goal_p == context.false:
        edge_pn = state_p & controller_pn
        state_p = context.let(next_to_prev, context.exist(prevs, edge_pn))
        steps |= edge_pn
    return steps

def get_steps_id2(policy, task_bdd, context):
    steps = context.false
    # We are misuing node_id_temp and _goal as a timestep counter
    state_p = context.exist(goals, task_bdd) & context.add_expr("node_id_temp = 0")
    goal_g = context.exist(prevs, task_bdd)
    controller_pn = context.exist(goals, policy & goal_g) & context.add_expr("node_id_goal = node_id_temp + 1")
    goal_p = context.let(goal_to_prev, goal_g)
    prevs2 = prevs + ["node_id_temp"]
    next_to_prev2 = next_to_prev | {"node_id_goal": "node_id_temp"}
    while state_p & goal_p == context.false:
        edge_pn = state_p & controller_pn
        state_p = context.let(next_to_prev2, context.exist(prevs2, edge_pn))
        steps |= edge_pn
    return steps

def decode(sol, var, context):
    val = 0
    for i,b in enumerate(context.vars[var]['bitnames']):
        val += sol[b]<<i
    return val

#TODO rename
# Requires that policy be determinized (use determinize2)
def get_edges(policy, task_bdd, context):
    steps = get_steps_id2(policy, task_bdd, context)
    steps = context.exist(item_vars + ["node_id_goal"], steps)
    #TODO manual decoding
    return [(decode(sol, "node_id_temp", context), decode(sol, "node_id_prev", context), decode(sol, "node_id_next", context)) for sol in context.bdd.pick_iter(steps)]

# task_bdd is built by first creating a task expr, then existing off the nexts, then picking and cubing it.
#TODO: is cube() faster?
def get_path_concrete_id(policy, task_bdd, context):
    # Get a concrete path
    current = task_bdd.pick()
    #TODO: this context cube thing is a hack
    path = [context.pick(context.bdd.cube(current))]
    goal_satisfied = mk_goal_satisfied_id(context)
    while True:
        #print(current)
        current_bdd = context.bdd.cube(current)
        next_temp = context.exist(prevs, current_bdd & policy)
        advice = context.let(next_to_prev, next_temp)
        #print(advice.count())
        current = advice.pick()
        # Check whether the goal is satisfied in the state given by the advice.
        if (next_temp & goal_satisfied).pick():
            break
        path.append(context.pick(context.bdd.cube(current)))
    return path

def get_first_step(policy, task_dict, context):
    # Get a concrete path
    task_bdd = context.assign_from(task_dict)
    return context.pick(task_bdd & policy)

def abstractify_info(ram_data):
    abstate = abstractify_state(ram_data, global_pos=True)
    abboss = abstractify_boss_info(ram_data, offset=0x2000)
    abstate.items = abstate.items | abboss
    return abstate

# MAPS STUFF

def mk_node_ids(rooms):
    all_nodes = []
    for r, room in rooms.items():
        for node in room.graph.name_node.keys():
            all_nodes.append(node)
    node_ids = {n:i for i,n in enumerate(all_nodes)}
    # Issue with design translation via chopping off the last _
    #node_ids["Spore_Spawn_Spawn"] = node_ids["Spore_Spawn_Spore_Spawn"]
    #node_ids["Golden_Torizo_Torizo"] = node_ids["Golden_Torizo_Golden_Torizo"]
    #node_ids["Mother_Brain_Brain"] = node_ids["Mother_Brain_Mother_Brain"]
    return node_ids

def mk_node_memaddrs(rooms):
    node_memaddrs = {}
    for r, room in rooms.items():
        for node in room.graph.name_node.keys():
            node_memaddrs[node] = room.mem_address
    return node_memaddrs

class MapsInfo(object):

    def __init__(self, rooms_path, exits_path, bin_path, rom_manager):
        self.rom_manager = rom_manager
        self.bin_path = bin_path
        self.rooms = parse_rooms(rooms_path)
        self.exits = parse_exits(exits_path)
        print("Parsing ROM...")
        self.parsed_rom = self.rom_manager.parse()
        print("Building Dicts...")
        self.all_posns = all_global_positions(self.rooms, self.parsed_rom)
        # Fix up all_posns
        self.all_posns["Bomb_Torizo_B"]
        self.all_posns["Bomb_Torizo_Bombs"] = self.all_posns["Bomb_Torizo_B"]
        del self.all_posns["Bomb_Torizo_B"]
        self.world = dictify_rooms(self.rooms, self.exits)
        self.node_ids = mk_node_ids(self.rooms)
        self.node_ids_rev = {i:n for n,i in self.node_ids.items()}
        self.node_memaddrs = mk_node_memaddrs(self.rooms)
        self.context = mk_context_id(self.node_ids)
        self.current_goal_node = "Landing_Site_End"
        self.item_nodes = set([])
        for r, room in self.rooms.items():
            for node in room.graph.name_node.keys():
                n = room.graph.name_node[node].data
                if isinstance(n, Item) or isinstance(n, Boss):
                    self.item_nodes.add(node)

    def read_state(self):
        ram_data = np.fromfile(self.bin_path, dtype="int16")
        return abstractify_info(ram_data)

    def estimate_state(self):
        ram_data = np.fromfile(self.bin_path, dtype="int16")
        return self.estimate_state_from_ram(ram_data)

    def estimate_state_from_ram(self, ram_data):
        abstate = abstractify_info(ram_data)
        current_room_a = ram_data.view("uint16")[0x79b // 2] >> 8
        current_room_b = (ram_data.view("uint16")[0x79c // 2] & 0x00ff) << 8
        current_room = current_room_a | current_room_b
        #dist, nearest_node = map_state_to_node(abstate, all_posns)
        #print(abstate.position)
        #print(dist, nearest_node)
        # Find a nearby node in the current room
        for r, room in self.rooms.items():
            if room.mem_address & 0xffff == current_room:
                for node in room.graph.name_node.keys():
                    if node in self.all_posns and abstate.position.euclidean(self.all_posns[node]) < 5:
                        return node, abstate.items
                # Assumes room mem addrs are unique
                break
        return None

    def loc_id(self, room_name, node_name, when="prev"):
        node_id = self.node_ids[f"{room_name}_{node_name}"]
        return f"node_id_{when} = {node_id}"

    def item_transitions(self, item_gained=None):
        if item_gained is None:
            return "(items_unchanged)"
        clauses = []
        for i in self.world["Items"] | self.world["Bosses"]:
            if i == item_gained:
                clause = f"{i}_prev < {i}_next"
            else:
                clause = f"{i}_prev = {i}_next"
            clauses.append(clause)
        return " & ".join(clauses)

    #TODO: merge these
    def itemset_to_str(self, itemset):
        if len(itemset) == 0:
            return "TRUE"
        else:
            return " & ".join([f"{item}_prev = 1" for item in itemset])

    def mk_itemset_expr(self, itemset, when="prev"):
        clauses = []
        for i in self.world["Items"]: # was item_mapping from data_types/itemset
            if i in itemset:
                clause = f"{i}_{when} = 1"
            else:
                clause = f"{i}_{when} = 0"
            clauses.append(clause)
        return " & ".join(clauses)

    def required_itemsets(self, itemsets):
        return "(" + " | ".join([itemset_to_str(itemset) for itemset in itemsets]) + ")"

    def get_first_step(self, policy, task_dict):
        # Get a concrete path
        task_bdd = self.context.assign_from(task_dict)
        return self.context.pick(task_bdd & policy)

    # Translate a state to BDD land
    # need current itemset, current node
    # state is from estimate_state
    def mk_task(self, state):
        node, items = state
        node_id = self.node_ids[node]
        current_nid = self.context.add_expr(f"node_id_prev = {node_id}")
        current_items = self.context.add_expr(self.mk_itemset_expr(items))
        task_expr = self.context.add_expr(f"node_id_goal = {self.node_ids[self.current_goal_node]}") & current_nid & current_items
        return task_expr

    def mk_task_concrete(self, state, policy):
        task_expr = self.mk_task(state)
        # Concrete task
        possible_tasks = self.context.exist(nexts, policy & task_expr)
        if possible_tasks.count() > 0:
            return self.context.pick(possible_tasks)
        # Gaslighting: You may be "at" a node that doesn't exist...
        # Prevents things like power bomb doors from screwing with things
        else:
            return None

    # Return the name of the node that Samus should visit next
    def get_step_advice(self, state, policy):
        task = self.mk_task_concrete(state, policy)
        if task is None:
            return None
        next = get_first_step(policy, task, self.context)
        return self.node_ids_rev[next["node_id_next"]]

    def get_path_advice(self, state, policy):
        # Make sure a path actually exists before trying to compute one
        task = self.mk_task_concrete(state, policy)
        if task is None:
            return None
        path = get_path_concrete_id(policy, self.context.assign_from(task), self.context)
        return [self.node_ids_rev[i["node_id_prev"]] for i in path]

    def get_edge_advice(self, state, policy):
        task = self.mk_task_concrete(state, policy)
        if task is None:
            return None
        edges = sorted(get_edges(policy, task, self.context))
        return edges
    # Yellow: current segment
    # Green: segment up to the next item
    # Grey: rest of the lines
    # state_estimate is (node, itemset)
    def generate_lines(self, state_estimate, policy):
        path = self.get_path_advice(state_estimate, policy)
        out = {
            "next_step": [],
            "next_item": [],
            "remaining_path": [],
        }
        # The "path" only makes sense if there's at least two locations
        if path is None or len(path) < 2:
            return out
        else:
            # Filter down to nodes that we know the location of
            #TODO: this has issues if there's an item node with an unknown location (e.g. a boss)
            which_current = "next_step"
            which_next = "next_step"
            for node in path:
                which_current = which_next
                out[which_current].append(node)
                # [a, b]
                # [b, c, ... e]
                # [e, ...]
                # Desired behavior: if the next node is an item node, next_item should be empty.
                if which_current == "next_step" and len(out["next_step"]) == 2:
                    which_next = "next_item"
                if which_current == "next_item" and node in self.item_nodes:
                    which_next = "remaining_path"
                if which_next != which_current:
                    out[which_next].append(node)
            return out
