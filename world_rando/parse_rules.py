from pathlib import Path
from PIL import Image
import numpy as np
from sm_rando.world_rando.rules import SamusState, LevelState, Rule, SamusPose, AbstractTile, SearchState, Transition
from sm_rando.world_rando.coord import Coord, Rect
from sm_rando.data_types.item_set import ItemSet

defaults = {
    "Cost": "0",
    "Items" : "",
    "b_Pose": "Stand",
    "b_vv": "0",
    "b_vh": "0",
    "a_Pose": "Stand",
    "a_vv": "0",
    "a_vh": "0"
    }

pose_str = {
    "Stand": SamusPose.STAND,
    "Morph": SamusPose.MORPH,
    "Jump": SamusPose.JUMP,
    "Spin": SamusPose.SPIN
    }

color_to_abstract = {
    (255, 255, 255) : AbstractTile.UNKNOWN,
    #TODO: samus might be underwater / ambiguous
    (255, 0, 0) : AbstractTile.AIR,
    (0, 255, 0) : AbstractTile.AIR,
    (251, 242, 54) : AbstractTile.AIR,
    (251, 137, 54) : AbstractTile.AIR_VERT_STOP,
    (178, 251, 54) : AbstractTile.AIR_HORIZ_STOP,
    (0, 0, 0) : AbstractTile.SOLID,
    (255, 22, 169) : AbstractTile.PLAN_SOLID,
    (119, 33, 105) : AbstractTile.GRAPPLE,
    (48, 185, 211) : AbstractTile.WATER,
    (48, 211, 151) : AbstractTile.WATER_VERT_STOP,
    (48, 117, 211) : AbstractTile.WATER_HORIZ_STOP,
    }

player_before_color = (255, 0, 0)
player_after_color = (0, 255, 0)

# Parse the level image to get the level definition for a rule
def make_level(image):
    level_array = np.zeros(image.size, dtype="int")
    player_before_pos = None
    player_after_pos = None
    for xy in Rect(Coord(0,0), Coord(image.size[0], image.size[1])):
        p = image.getpixel((xy.x, xy.y))
        m = color_to_abstract[p]
        if p == player_before_color and player_before_pos is None:
            player_before_pos = xy
        if p == player_after_color and player_after_pos is None:
            player_after_pos = xy
        level_array[(xy.x, xy.y)] = m
    level = LevelState(Coord(0,0), level_array)
    return player_before_pos, player_after_pos, level

def get_rule_name(rule_lines):
    l, r = rule_lines[0].split(":")
    return r.strip()

def get_rule_dict(rule_lines):
    d = {}
    for line in rule_lines:
        # Special flags
        if line.strip() == "NH":
            d["NH"] = ""
        else:
            l,r = line.split(":")
            d[l.strip()] = r.strip()
    # Add defaults
    for k,v in defaults.items():
        if k not in d:
            d[k] = v
    return d

def parse_interval(interval_str):
    constraints = interval_string.split("<=")
    l = -float("inf")
    r = float("inf")
    if len(constraints) == 3:
        l, c, r = l
        l = int(l)
        r = int(r)
    elif len(constraints) == 2:
        l, r = constraints
        if l == "X":
            c = l
            r = int(r)
        elif r == "X":
            c = r
            l = int(l)
        else:
            assert False
    elif len(constraints) == 1:
        c = constraints[0]
    assert c == "X"
    return Interval(l, r)

def parse_items(items_str):
    items = [i.strip() for i in items_str.split(",")]
    s = ItemSet()
    for i in items:
        if len(i) > 0:
            s.add(i)
    return s

def make_rule(rules_path, rule_lines, all_rules):
    d = get_rule_dict(rule_lines)
    rule_name = d["Rule"]
    rules_pic_path = rules_path / (rule_name + ".png")
    level_image = Image.open(rules_pic_path)
    b_pos, a_pos, level = make_level(level_image)
    assert b_pos is not None
    assert a_pos is not None
    items = parse_items(d["Items"])
    b_vv = get_b_velocity(d["b_vv"])
    b_vh = get_b_velocity(d["b_vh"])
    b_state = SamusState(b_pos, int(d["b_vv"]), int(d["b_vh"]), items, pose_str[d["b_Pose"]])
    a_state = SamusState(a_pos, int(d["a_vv"]), int(d["a_vh"]), items, pose_str[d["a_Pose"]])
    final_state = SearchState(a_state, level)
    t = Transition(b_state, final_state)
    rule =  Rule(d["Rule"], [t], int(d["Cost"]))
    # Also include the horizontal flip
    if "NH" not in d:
        return [rule, rule.horizontal_flip()]
    else:
        return [rule]

def make_rule_chain(rule_lines, all_rules):
    rule_name = get_rule_name(rule_lines)
    reference_rules = [n.strip() for n in rule_name.split(",")]
    assert len(reference_rules) > 1, "Rule chain with only one reference: {}".format(rule_name)
    # Check validity of references
    for r in reference_rules:
        assert r in all_rules, "Bad rule reference in rule chain: {}".format(r)
    rules = [all_rules[r] for r in reference_rules]
    return reduce(lambda x,y: x + y, rules)

def get_b_velocity(entry):
    if entry == "BIND>0":
        return Bind.BIND_GT
    elif entry == "BIND>=0":
        return Bind.BIND_GEQ
    elif entry == "BIND<0":
        return Bind.BIND_LT
    elif entry == "BIND<=0":
        return Bind.BIND_LEQ
    elif entry == "BIND":
        return Bind.BIND
    else:
        return int(entry)

def make_test_state(rules_path, rule_lines):
    d = get_rule_dict(rule_lines)
    rule_name = d["Test"]
    rules_pic_path = rules_path / (rule_name + ".png")
    level_image = Image.open(rules_pic_path)
    b_pos, a_pos, level = make_level(level_image)
    assert b_pos is not None
    assert a_pos is not None
    items = parse_items(d["Items"])
    b_vv = get_b_velocity(d["b_vv"])
    b_vh = get_b_velocity(d["b_vh"])
    b_state = SamusState(b_pos, b_vv, b_vh, items, pose_str[d["b_Pose"]])
    a_state = SamusState(a_pos, int(d["a_vv"]), int(d["a_vh"]), items, pose_str[d["a_Pose"]])
    initial_state = SearchState(b_state, level)
    final_state = a_state
    return initial_state, final_state

def parse_rules(rules_file):
    # Path to directory where the rules.txt lives
    rules_path = Path(rules_file).parents[0]
    f = open(rules_file, "r")
    all_rule_lines = []
    current_rule_lines = []
    for line in f.readlines():
        line = line.strip()
        # Blank Line means new rule
        if len(line) == 0:
            all_rule_lines.append(current_rule_lines)
            current_rule_lines = []
        elif line[0] == "#":
            continue
        else:
            current_rule_lines.append(line)
    # Append the last room
    all_rule_lines.append(current_rule_lines)
    #print(all_rule_lines)
    rules = {}
    tests = {}
    for rule_lines in all_rule_lines:
        if len(rule_lines) >= 1:
            l,r = rule_lines[0].split(":")
            rule_name = r.strip()
            if l == "Chain":
                #print("Chain: {}".format(rule_name))
                rule = make_rule_chain(rule_lines, rules)
                rules[rule.name] = rule
            elif l == "Rule":
                #print("Rule: {}".format(rule_name))
                made_rules = make_rule(rules_path, rule_lines, rules)
                for r in made_rules:
                    rules[r.name] = r
            elif l == "Test":
                #print("Test: {}".format(rule_name))
                test = make_test_state(rules_path, rule_lines)
                tests[rule_name] = test
    f.close()
    return rules, tests
