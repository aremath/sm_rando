import itertools
import random
from encoding import sm_global

def parse_preds(pred_file):
    f = open(pred_file, "r")
    preds = []
    for line in f.readlines():
        if line[0] == "\n":
            continue
        if line[0] == "#":
            continue
        else:
            preds.extend(parse_pred_expr(line))
    return preds

def filter_preds(to_place, preds):
    """
    Filter out predicates that do not apply to the given list of entities that are being ordered
    """
    return [(a, b) for a,b in preds if a in to_place and b in to_place]

def parse_pred_expr(pred):
    groups = pred.split("<")
    # 1 group means this expression doesn't have semantic meaning
    if len(groups) == 1:
        return []
    # take care of extra characters
    groups = [group.strip().strip("()").split() for group in groups]
    # take the cartesian product of every g1 g2 where g1 < g2
    preds = []
    for i1, g1 in enumerate(groups):
        for i2, g2 in enumerate(groups):
            if i1 < i2:
              preds.extend(itertools.product(g1, g2))
    return preds

#TODO: this may not be very uniform, and it may get stuck, even with satisfiable preds (?)
def choose_order(preds, to_place):
    """Choose an order for to_place that respects preds"""
    # Copy since this process is destructive to to_place
    to_place = to_place[:]
    # Invariant - every item in placed respects preds
    placed = []
    while len(to_place) > 0:
        # Choose an item to place, and remove it from to_place
        can = can_place(preds, to_place)
        if len(can) == 0:
            raise ValueError("No possible ordering")
        place = random.choice(can)
        placed.append(place)
        to_place.remove(place)
        # Update preds: we've satisfied constraints on place
        preds = [pred for pred in preds if pred[0] != place]
    return placed

def can_place(preds, to_place):
    """Find the items that can be placed, respecting preds"""
    can = []
    for item in to_place:
        # place the item if there is nothing in preds that constrains it
        if len([pred for pred in preds if pred[1] == item]) == 0:
            can.append(item)
    return can

# For a full design, use list(sm_global.all_things)
def order(things, fname="encoding/dsl/item_order.txt"):
    preds = filter_preds(things, parse_preds(fname))
    return choose_order(preds, things)

# For a full design, use list(sm_global.regions.keys())
def region_order(regions, fname="encoding/dsl/region_order.txt"):
    preds = filter_preds(regions, parse_preds(fname))
    return choose_order(preds, regions)

