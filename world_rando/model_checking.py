from pyModelChecking import *
from pyModelChecking.CTL import *
from itertools import product, chain, combinations
from pathlib import Path
import numpy as np

from rules import *
import parse_rules

no_softlocks = AG(EF("goal"))
# TODO: you cannot return to the start state because picking up items is one-way
# Instead, we want to be able to return to the start POSITION
return_to_start = AG(EF("start"))
reach_goal = EF("goal")

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

def verify(test, spec, rules):
    initial_state, final_state = test
    i_samus = initial_state.samus
    level = initial_state.level
    # Check the level for no blank tiles
    for i in np.nditer(level.level):
        assert i != AbstractTile.UNKNOWN
    x_range = range(level.shape[0])
    y_range = range(level.shape[1])
    initial_items = i_samus.items
    # Powerset of obtainable items is all possible item states within the level
    item_sets = all_itemsets(initial_items, level.items.values())
    states = []
    transitions = []
    labels = {}
    labels[final_state] = ["goal"]
    labels[i_samus] = ["start"]
    yvs = range(-1,6)
    #TODO also check other velocity types
    xvs = range(-velocity_maxima[VType.RUN], velocity_maxima[VType.RUN])
    all_valid_states = set()
    for s in iter_all_states(x_range, y_range, xvs, yvs, item_sets):
        # Only consider states where samus is not inside an object
        if check_samus_pos(level, s):
            all_valid_states.add(s)
    for s in all_valid_states:
        # Can stay still (function must be left-total)
        transitions.append((s,s))
        ss = SearchState(s, level)
        new_states = [r.apply(ss) for r in rules]
        for next_state, err in new_states:
            if next_state is not None:
                next_samus = next_state.samus
                if next_samus not in all_valid_states:
                    print("ASSERT")
                    print(next_samus.position)
                    print(next_samus.velocity)
                    print(next_samus.items)
                    print(next_samus.pose)
                    assert False
                if check_samus_pos(level, next_samus):
                    transitions.append((s, next_samus))
    #TODO: optionally other labels
    #assert i_samus in states
    k = Kripke(S=all_valid_states,S0=[i_samus],R=transitions,L=labels)
    sat_states = modelcheck(k, spec)
    # Spec holds if it is true at the start state
    return (i_samus in sat_states)

if __name__ == "__main__":
    rules_file = Path("../encoding/rules/rules.yaml")
    rules, tests = parse_rules.parse_rules_yaml(rules_file)
    t = verify(tests["TestGrabBombsVerify"], no_softlocks, rules.values())
    print(t)
