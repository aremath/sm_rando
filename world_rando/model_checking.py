# Pretend to be in top-level directory to get the imports to play nice
import sys
sys.path.append("..")

from pyModelChecking import *
from pyModelChecking.CTL import *
from itertools import product, chain, combinations
from pathlib import Path
import numpy as np
from tqdm import tqdm
import time
import graphviz
import pickle

#import parse_rules
#from world_rando import parse_rules
#from rules import *
#from search import *
from world_rando import parse_rules
from world_rando.rules import *
from world_rando.search import *

no_softlocks = AG(EF("goal"))
no_softlocks_inner = EF("goal")
# TODO: you cannot return to the start state because picking up items is one-way
# Instead, we want to be able to return to the start POSITION
return_to_start = AG(EF("start"))
return_to_start_inner = EF("start")
reach_goal = EF("goal")

counterexample_color = (255, 0, 0)

def powerset(iterable):
    n = len(iterable)
    for r in range(n+1):
        for combination in combinations(iterable, r):
            yield combination

def all_itemsets(start_items, gain_items):
    out = []
    for p in powerset(gain_items):
        s = start_items
        for i in p:
            s = s | i
        out.append(s)
    return out

def check_samus_pos(level, state):
    pos = state.position
    pose = state.pose
    tiles = samus_tiles(pos, pose)
    level_array = level.level
    origin = level.origin
    for t in tiles:
        # Allow samus in any state where tiles can be treated as air
        if not level_check(level_array, origin, t, AbstractTile.AIR, state):
            return False
    return True

def add_position_label(label_word, labels, states, position):
    s = [s for s in states if s.position == position]
    for state in s:
        if state in labels:
            labels[state].append(label_word)
        else:
            labels[state] = [label_word]

def iter_all_states(x_range, y_range, xvs, yvs, item_sets):
    for x,y,vx,vy,i,p in product(x_range, y_range, xvs, yvs, item_sets, SamusPose):
        pos = Coord(x,y)
        hv = HVelocity(VType.RUN, vx)
        v = Velocity(vy, hv)
        s = SamusState(pos, v, i, p)
        yield s

#TODO: export a networkx graph building function

def make_kripke(initial_state, final_state, level, rules):
    # Check the level for no blank tiles
    for i in np.nditer(level.level):
        assert i != AbstractTile.UNKNOWN
    x_range = range(level.shape[0])
    y_range = range(level.shape[1])
    initial_items = initial_state.items
    # Powerset of obtainable items is all possible item states within the level
    item_sets = all_itemsets(initial_items, level.items.values())
    states = []
    transitions = []
    labels = {}
    labels[final_state] = ["goal"]
    labels[initial_state] = ["start"]
    yvs = range(-1,6)
    #TODO also check other velocity types
    xvs = range(-velocity_maxima[VType.RUN], velocity_maxima[VType.RUN])
    all_valid_states = set()
    # Find valid states
    time_a = time.perf_counter()
    o, f, p = rule_search(SearchState(initial_state, level), rules, None)
    all_valid_states = set([f_i.samus for f_i in f])
    time_b = time.perf_counter()
    print("Enumerated {} states in {} seconds".format(len(all_valid_states), time_b - time_a))
    # Build the graph
    for s in tqdm(all_valid_states):
        # Can stay still (function must be left-total)
        transitions.append((s,s))
        ss = SearchState(s, level)
        new_states = [r.apply(ss) for r in rules]
        for r, (next_state, err) in zip(rules, new_states):
            if next_state is not None:
                next_samus = next_state.samus
                next_samus = next_state.samus
                # As a sanity check, ensure that you can't go out of bounds by applying rules
                if next_samus not in all_valid_states:
                    print("ASSERT")
                    print(r.name)
                    print(s)
                    print(next_samus)
                    assert False
                if check_samus_pos(level, next_samus):
                    transitions.append((s, next_samus))
    #TODO: optionally other labels
    print("Number of States: {}".format(len(all_valid_states)))
    initial_states = set([initial_state])
    k = Kripke(S=all_valid_states,S0=initial_states,R=transitions,L=labels)
    time_c = time.perf_counter()
    print("Built graph with {} edges in {} seconds".format(len(transitions), time_c - time_b))
    return initial_states, k

def find_counterexample(initial_states, sat_states, k, ag_formula, inner_formula):
    # Sanity check - provide both AG(F) and F
    assert AG(inner_formula) == ag_formula
    # Can't find a counterexample if the formula was actually satisfied
    assert not initial_states <= sat_states
    # If AG(F) is not satisfied by K, then EF(not F) is satisfied by K
    # The counterexample is a path to a state where not F holds
    # First compute the set of states where F holds:
    inner_holds = modelcheck(k, inner_formula)
    # Now BFS through states where AG(F) does not hold (starting with the initial state)
    # to find a state where not F holds
    offers = {}
    finished = set()
    final_state = None
    queue = list(initial_states)
    while len(queue) > 0:
        state = queue.pop(0)
        # If F does not hold at the current state, we are done
        if state not in inner_holds:
            final_state = state
        next_states = k.next(state)
        for next_state in next_states:
            if next_state not in finished:
                finished.add(next_state)
                offers[next_state] = state
                queue.append(next_state)
    # Since AG(F) does not hold, this should never fire
    assert final_state is not None, "No path found!"
    # Now use offers to decode the path that was used
    path = []
    current_state = final_state
    print(k.next(final_state))
    while current_state not in initial_states:
        path.insert(0, current_state)
        current_state = offers[current_state]
    # Append the final current_state which is an initial state
    path.insert(0, current_state)
    return path


def verify(test, rules, spec, output=None, inner_spec=None):
    i_state, final_state = test
    initial_state = i_state.samus
    level = i_state.level
    initial_states, k = make_kripke(initial_state, final_state, level, rules)
    kripke_to_dot(k, output)
    time_a = time.perf_counter()
    sat_states = modelcheck(k, spec)
    time_b = time.perf_counter()
    print("Checked model in {} seconds".format(time_b - time_a))
    # Spec holds if it is true at the start state
    if initial_states <= sat_states:
        return True, k, None
    else:
        # Find a counterexample path if desired
        if inner_spec is not None:
            path = find_counterexample(initial_states, sat_states, k, spec, inner_spec)
            print(path)
            path_positions = [s.position for s in path]
            # Now path is the counterexample. Draw it using the level:
            out_image = level.to_image(path_positions, counterexample_color)
            # Save it
            out_path = output / "counterexample.png"
            out_image.save(out_path)
            # Pretty print it
            out_pretty = level.pretty_print(path, "../encoding/levelstate_tiles")
            out_pretty.save(out_path)
        return False, k, path

def kripke_to_dot(k, out_path):
    g = graphviz.Digraph()
    state_set = set(k.states())
    state_ids = {k:i for i,k in enumerate(state_set)}
    for state in state_set:
        state_id = str(state_ids[state])
        g.node(state_id)
    for s1, s2 in k.transitions():
        s1_id = str(state_ids[s1])
        s2_id = str(state_ids[s2])
        g.edge(s1_id, s2_id)
    with open(out_path / "model_graph.dot", "w") as f:
        f.write(str(g))
    with open(out_path / "kripke", "wb") as f:
        pickle.dump(k, f)

if __name__ == "__main__":
    out_path = Path("../output")
    rules, tests = parse_rules.parse_rules(["../encoding/rules/rules.yaml",
        "../encoding/rules/model_checking_tests/model_checking_tests.yaml"])
    t, _, _ = verify(tests["ModifiedConstructionZone2"], rules.values(), no_softlocks, out_path, no_softlocks_inner)
    #t = verify(tests["ConstructionSub"], rules.values(), no_softlocks, out_path, no_softlocks_inner)
    print(t)
