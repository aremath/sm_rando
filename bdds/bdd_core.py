from omega.symbolic.fol import Context
import itertools
from tqdm import tqdm

from world_rando.rules import *
from data_types.item_set import item_mapping
from world_rando.parse_rules import parse_rules, make_level_from_room
from world_rando.coord import Coord

rules, tests = parse_rules(["../encoding/rules/rules.yaml"])

# Theoretical max is probably 20x20
MAX_LEVEL_SIZE = 20 * 16

def mk_context():
    context = Context()
    context.declare(
        # Higher is more granular
        granularity = (0,1),
        room_id_prev = (0,0xffff),
        room_id_next = (0,0xffff),
        room_id_goal = (0,0xffff),
        room_id_temp = (0,0xffff),

        rule = (0,len(rules.keys())-1),

        x_prev = (0,MAX_LEVEL_SIZE-1),
        x_next = (0,MAX_LEVEL_SIZE-1),
        x_goal = (0,MAX_LEVEL_SIZE-1),
        x_temp = (0,MAX_LEVEL_SIZE-1),

        y_prev = (0,MAX_LEVEL_SIZE-1),
        y_next = (0,MAX_LEVEL_SIZE-1),
        y_goal = (0,MAX_LEVEL_SIZE-1),
        y_temp = (0,MAX_LEVEL_SIZE-1),

        pose_prev = (0,len(SamusPose)-1),
        pose_next = (0,len(SamusPose)-1),
        pose_goal = (0,len(SamusPose)-1),
        pose_temp = (0,len(SamusPose)-1),

        vt_prev = (0, len(VType)),
        vt_next = (0, len(VType)),
        vt_goal = (0, len(VType)),
        vt_temp = (0, len(VType)),

        vh_prev = (-30, 30),
        vh_next = (-30, 30),
        vh_goal = (-30, 30),
        vh_temp = (-30, 30),

        vv_prev = (-15, 1),
        vv_next = (-15, 1),
        vv_goal = (-15, 1),
        vv_temp = (-15, 1),
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
    return context

# Used for populating various entries like prev_to_next
default_context = mk_context()

def mk_replace(context, before, after):
    replace_dict = {}
    for k in context.vars.keys():
        if k.endswith(before):
            replace_dict[k] = k.replace(before, after)
    return replace_dict

def translate_iset(itemset, fstr="{}"):
    d = {}
    for i in item_mapping:
        if i in itemset:
            d[fstr.format(i)] = 1
        #else:
        #  d[fstr.format(i)] = 0
    return d

all_xys = ["x_prev", "y_prev", "x_next", "y_next"]
nonxy_prev = list(filter(lambda x: x != "x_prev" and x != "y_prev", default_context.vars.keys()))
nonxy_next = list(filter(lambda x: x != "x_next" and x != "y_next", default_context.vars.keys()))
nonxy_all = list(filter(lambda x: x not in all_xys, default_context.vars.keys()))

def get_posns(trans, context):
    posns = context.exist(nonxy_all, trans)
    next_posns = [(a["x_next"], -a["y_next"]) for a in context.pick_iter(posns)]
    prev_posns = [(a["x_prev"], -a["y_prev"]) for a in context.pick_iter(posns)]
    return next_posns + prev_posns

def mk_trans(room_header, context):
    level = make_level_from_room(room_header)
    trans = context.false
    addr = int(room_header.old_address) & 0xffff
    room_same = context.add_expr(f"room_id_prev = {addr} & room_id_next = {addr}")
    for i,(x,y) in tqdm(enumerate(itertools.product(range(level.shape[0]), range(level.shape[1]))), total=level.shape[0] * level.shape[1]):
        c = Coord(x, y)
        for name, rule in rules.items():
            #print(c, name)
            expr = rule.level_transition.as_tla(c, level)
            if expr:
                #print(c, name)
                #print(expr)
                #TODO: context.define(items_unchanged)
                #TODO: pass context to as_tla and produce a BDD
                expr_bdd = context.add_expr(expr, with_ops=True)
                #print(f"Expr: {expr_bdd.count()}")
                #print(f"Room Same: {room_same.count()}")
                #print(f"Combined: {(expr_bdd & room_same).count()}")
                trans |= (expr_bdd & room_same)
    return trans

# Have: trans(prev, next)
# Want: trans(temp, next)
# Have: closure(prev, next)
# Want: closure(prev, temp)
prev_to_temp = mk_replace(default_context, "prev", "temp")
next_to_temp = mk_replace(default_context, "next", "temp")
goal_to_next = mk_replace(default_context, "goal", "next")
prev_to_next = mk_replace(default_context, "prev", "next")
next_to_prev = mk_replace(default_context, "next", "prev")
temps = [k for k in default_context.vars.keys() if k.endswith("_temp")]
nexts = [k for k in default_context.vars.keys() if k.endswith("_next")]
prevs = [k for k in default_context.vars.keys() if k.endswith("_prev")]
goals = [k for k in default_context.vars.keys() if k.endswith("_goal")]

# Iterative squaring
# Remember to first project over "rule" with trans_norule = context.exist(["rule"], trans)
def mk_closure(trans_norule, context):
    n = 0
    closure = trans_norule
    closure_last = context.false
    while closure != closure_last:
        closure_last = closure
        closure_prev_temp = context.let(next_to_temp, closure_last)
        closure_temp_next = context.let(prev_to_temp, closure_last)
        closure |= context.exist(temps, closure_prev_temp & closure_temp_next)
        print(n, closure.dag_size)
        n+=1
    closure_square = closure
    return closure_square

# Needs recursion limit = 3k
def mk_door_trans(door_tla_path, context):
    # output/doors.tla
    with open(door_tla_path) as f:
        s = f.read()
        door_trans = context.add_expr(s)
    return door_trans

def mk_goal_satisfied(context):
    # Expression that holds when the goal is satisfied (for all possible goals)
    goal_satisfied = context.true
    for v1, v2 in zip(nexts, goals):
        sat = context.add_expr(f"{v1} = {v2}")
        #print(sat.dag_size)
        #print(goal_satisfied.dag_size)
        goal_satisfied &= sat
    return goal_satisfied

# covered = goal_satisfied
# while covered keeps changing:
#   covered |= exist prev s.t. covered(next, goal) and trans(prev, next)
def mk_policy(trans_norule, context):
    n = 0
    # prev, next, goal
    policy_png = context.false
    covered_ng = mk_goal_satisfied(context)
    covered_last_ng = context.false
    while covered_ng != covered_last_ng:
        # States with edges into a covered state
        covered_last_ng = covered_ng
        covered_pg = context.let(next_to_prev, covered_ng)
        fringe_png = trans_norule & covered_ng & ~covered_pg
        policy_png |= fringe_png
        # Find a state in covered that the fringe state transitions to
        covered_ng |= context.let(prev_to_next, context.exist(nexts, fringe_png))
        print(n, fringe_png.dag_size, covered_ng.dag_size, policy_png.dag_size)
        n += 1
    return policy_png

def determinize(policy, context):
    fns = make_functions(policy, bits, policy.bdd)
    deterministic_policy = context.bdd.add_expr(f"&".join([f"({k} <-> {v['function']})" for k,v in fns.items()]))
    return deterministic_policy

# task_bdd is built by first creating a task expr, then existing off the nexts, then picking and cubing it.

def get_path_concrete(policy, task_bdd, context):
    # Get a concrete path
    current = task_bdd.pick()
    path = [current]
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
        path.append(current)
    return path

def get_path_symbolic(policy, task_bdd, context):
    keep_vars = ["x_prev", "y_prev", "room_id_prev", "x_next", "y_next", "room_id_next", "M_prev", "M_next"]
    exist_vars = list(filter(lambda x: x not in keep_vars, context.vars.keys()))
    current_state = context.exist(goals, task_bdd)
    goal_bdd = context.exist(prevs, task_bdd)
    path = []
    while True:
        next_state_bdd = context.assign_from(context.pick(context.exist(prevs, current_state & policy & goal_bdd)))
        print()
        print(context.pick(context.exist(exist_vars, current_state)))
        print(context.pick(context.exist(exist_vars, next_state_bdd)))
        current_state = context.let(next_to_prev, next_state_bdd)
        if (goal_satisfied & next_state_bdd).count() > 0:
            break

def room_addr_tla(room_header):
    return f"room_id_prev = {int(room_header.old_address) & 0xffff}"

# Restrict door_trans a certain set of rooms
def mk_door_trans_for_rooms(door_trans, rooms, context):
    room_restriction = context.add_expr(" | ".join([room_addr_tla(r) for r in rooms]))
    return door_trans & room_restriction
