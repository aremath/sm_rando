import itertools
import random

items = ["B", "PB", "SPB", "S", "M", "G", "SA", "V", "GS", "SB", "MB", "CB", "WB", "E", "PLB", "IB", "HJ", "SJ", "Spazer"]
bosses = ["Kraid", "Phantoon", "Draygon", "Ridley"]
all_things = items + bosses

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

def choose_order(preds, to_place):
    """Choose an order for to_place that respects preds"""
    # invariant - every item in placed respects preds
    placed = []
    while len(to_place) > 0:
        #choose an item to place, and remove it from to_place
        can = can_place(preds, to_place)
        if len(can) == 0:
            return -1
        place = random.choice(can)
        placed.append(place)
        to_place.remove(place)
        # update preds: we've satisfied constraints on place
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

def order():
    preds = parse_preds("encoding/dsl/item_order.txt")
    return choose_order(preds, all_things)
