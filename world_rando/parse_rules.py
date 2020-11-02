from pathlib import Path
from PIL import Image
import numpy as np
import yaml
from sm_rando.world_rando.rules import *
from sm_rando.world_rando.coord import Coord, Rect
from sm_rando.data_types.item_set import ItemSet

def reverse_dict(d):
    return {v:k for k,v in d.items()}

defaults = {
    "cost": "0",
    "items" : "",
    "obtain" : "",
    "b_pose": "Stand",
    "b_vv": "0",
    "b_vh": "Run,0",
    "a_pose": "Stand",
    "a_vv": "0,Lose",
    "a_vh": "Run,0,Lose"
    }

pose_str = {
    "Stand": SamusPose.STAND,
    "Morph": SamusPose.MORPH,
    "Jump": SamusPose.JUMP,
    "Spin": SamusPose.SPIN
    }

vtype_str = {
    "Run": VType.RUN,
    "Water": VType.WATER,
    "Speed": VType.SPEED
    }

vbehave_str = {
    "Lose": VBehavior.LOSE,
    "Store": VBehavior.STORE
    }

color_to_abstract = {
    (255, 255, 255) : AbstractTile.UNKNOWN,
    (255, 0, 0) : AbstractTile.AIR,
    (0, 255, 0) : AbstractTile.AIR,
    (251, 242, 54) : AbstractTile.AIR,
    (0, 0, 0) : AbstractTile.SOLID,
    (119, 33, 105) : AbstractTile.GRAPPLE,
    #(48, 185, 211) : AbstractTile.WATER,
    #TODO: samus might be underwater / ambiguous
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
    #TODO: water stuff
    # water level is between the lowest air and the highest water
    level = LevelState(Coord(0,0), level_array, LiquidType.NONE, float("inf"))
    return player_before_pos, player_after_pos, level

def add_defaults(rule_dict):
    d = {k:v for k,v in rule_dict.items()}
    for k,v in defaults.items():
        if k not in d:
            d[k] = v
    return d

def parse_end_vv(vstr):
    v_move_s, v_behave_s = vstr.split(",")
    v_move = int(v_move_s)
    v_behave = vbehave_str[v_behave_s]
    return v_move, v_behave

def parse_end_vh(vstr):
    v_type_s, v_move_s, v_behave_s = vstr.split(",")
    v_move = int(v_move_s)
    v_behave = vbehave_str[v_behave_s]
    v_type = vtype_str[v_type_s]
    return v_type, v_move, v_behave

def parse_end_v(d):
    vh_type, vh_move, vh_behave = parse_end_vh(d["a_vh"])
    vv_move, vv_behave = parse_end_vv(d["a_vv"])
    vh = HVelocity(vh_type, vh_move)
    return Velocity(vv_move, vh), vh_behave, vv_behave

def parse_vfunction(d):
    vh_types_s, vh_int_s = d["b_vh"].split(",")
    vv_int_s = d["b_vv"]
    vh_int = parse_interval(vh_int_s)
    vv_int = parse_interval(vv_int_s)
    vh_types_set = frozenset([vtype_str[i] for i in vh_types_s.split("|")])
    vh_set = HVelocitySet(vh_types_set, vh_int)
    domain = VelocitySet(vv_int, vh_set)
    v_end, vh_behave, vv_behave = parse_end_v(d)
    return VelocityFunction(domain, vv_behave, vh_behave, v_end)

def parse_interval(interval_string):
    """ Parses intervals of the form
    1 <= X <= 2
    X <= 2
    1 <= X
    4 (means X = 4 or 4 <= X <= 4)
    """
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
        # Allow single integer
        if c != "X":
            a = int(c)
            c = "X"
            l = a
            r = a
    assert c == "X"
    return Interval(l, r)

def parse_items(items_str):
    items = [i.strip() for i in items_str.split(",")]
    s = ItemSet()
    for i in items:
        if len(i) > 0:
            s.add(i)
    return s

def make_rule(level_image, rule_lines):
    rule_name = d["Rule"]
    b_pos, a_pos, level = make_level(level_image)
    assert b_pos is not None
    assert a_pos is not None
    items = parse_items(d["items"])
    b_vv = get_b_velocity(d["b_vv"])
    b_vh = get_b_velocity(d["b_vh"])
    b_state = SamusState(b_pos, int(d["b_vv"]), int(d["b_vh"]), items, pose_str[d["b_pose"]])
    a_state = SamusState(a_pos, int(d["a_vv"]), int(d["a_vh"]), items, pose_str[d["a_pose"]])
    final_state = SearchState(a_state, level)
    t = Transition(b_state, final_state)
    rule =  Rule(d["Rule"], [t], int(d["cost"]))
    # Also include the horizontal flip
    if "Symmetric" not in d:
        return [rule, rule.horizontal_flip()]
    else:
        return [rule]

def index_level(level, coord):
    """ Bounds-checking: out-of-bounds is unknown """
    if coord.x >= 0 and coord.y >= 0:
        try:
            return level[coord]
        except IndexError:
            return AbstractTile.UNKNOWN
    # Negative indices are out of bounds (don't wrap)
    else:
        return AbstractTile.UNKNOWN

def get_all(level, tile_list, tile_type):
    return [tile for tile in tile_list if index_level(level, tile) == tile_type]

def normalize_list(coord_list, pos):
    return [l - pos for l in coord_list]

def parse_statefunction(name, level_image, d):
    #print("Parsing rule: {}".format(name))
    a_items, b_items = get_items(d)
    b_pos, a_pos, level = make_level(level_image)
    scan_direction = (a_pos - b_pos).sign()
    r = Rect(Coord(0,0), Coord(level.shape[0], level.shape[1]))
    vf = parse_vfunction(d)
    p_initial = Coord(0,0)
    v_final = vf.domain
    pose_initial = pose_str[d["b_pose"]]
    pose_final = pose_str[d["a_pose"]]
    items_initial = parse_items(d["items"])
    items_obtained = parse_items(d["obtain"])
    sfunction = SamusFunction(vf, items_initial, items_obtained, pose_initial, pose_final, a_pos)
    #TODO: certain (i.e. the first of each rule) IntermediateStates hold the sfunction so that samus' state
    # can be inferred within the rule
    #TODO: verify by checking that the inferred end state is the same as the end state achieved through function
    # composition
    i_states = []
    for xy in r.iter_direction(scan_direction):
        s_t = samus_tiles(xy, pose_final)
        level_t = [index_level(level, t) for t in s_t]
        #If samus is here through the rule
        if all([t == AbstractTile.AIR for t in level_t]):
            # Note the position, nearby airs, and nearby walls
            all_adj = get_all_adj(xy, pose_final)
            walls = get_all(level, all_adj, AbstractTile.SOLID)
            # Normalized
            walls = normalize_list(walls, xy)
            airs = []
            # Collect the necessary airs for each direction
            for direction in [Coord(scan_direction.x, 0), Coord(0, scan_direction.y)]:
                airs_in_d = get_all(level, get_adj(xy, pose_final, direction), AbstractTile.AIR)
                airs_in_d = normalize_list(airs_in_d, xy)
                airs.append((direction, airs_in_d))
            # The position of this intermediate state relative to the origin
            rel_pos = xy - b_pos
            i_states.append(IntermediateState(rel_pos, walls, airs, None))
    if len(i_states) > 0:
        # Applies the function at the beginning of the rule
        i_states[0].samusfunction = sfunction
    #TODO liquid stuff
    ltype = LiquidType.NONE
    li = Interval(-float("inf"), float("inf"))
    lfunction = LevelFunction(ltype, li, i_states)
    cost = int(d["cost"])
    s = StateFunction(name, sfunction, lfunction, cost)
    if "Symmetric" not in d:
        return [s, s.horizontal_flip()]
    else:
        return [s]

def make_rule_chain(d, all_rules):
    rule_name = d["Chain"]
    reference_rules = [n.strip() for n in rule_name.split(",")]
    assert len(reference_rules) > 1, "Rule chain with only one reference: {}".format(rule_name)
    # Check validity of references
    for r in reference_rules:
        assert r in all_rules, "Bad rule reference in rule chain: {}".format(r)
    rules = [all_rules[r] for r in reference_rules]
    return reduce(lambda x,y: x + y, rules)

def get_items(d):
    b_items = parse_items(d["items"])
    a_items = b_items | parse_items(d["obtain"])
    return b_items, a_items

def get_v(d, t):
    vh_type_s, vh_int_s = d[t + "_vh"].split(",")
    vh_type = vtype_str[vh_type_s]
    vh = HVelocity(vh_type, int(vh_int_s))
    return Velocity(int(d[t + "_vv"]), vh)

def make_test_state(level_image, d):
    b_pos, a_pos, level = make_level(level_image)
    assert b_pos is not None
    assert a_pos is not None
    b_items, a_items = get_items(d)
    b_v = get_v(d, "b")
    a_v = get_v(d, "a")
    b_state = SamusState(b_pos, b_v, b_items, pose_str[d["b_pose"]])
    a_state = SamusState(a_pos, a_v, a_items, pose_str[d["a_pose"]])
    initial_state = SearchState(b_state, level)
    final_state = a_state
    return initial_state, final_state

def parse_rules_yaml(rules_file):
    # Path to directory where the rules.txt lives
    rules_path = Path(rules_file).parents[0]
    f = open(rules_file, "r")
    rules_yaml = yaml.load(f)
    rules = {}
    tests = {}
    if rules_yaml["Rules"] is not None:
        for r_dict in rules_yaml["Rules"]:
            rule_name = list(r_dict.keys())[0]
            print("Rule: {}".format(rule_name))
            rule_definition = r_dict[rule_name]
            if rule_definition is None:
                rule_definition = {}
            r_dict = add_defaults(rule_definition)
            pic_path = rules_path / (rule_name + ".png")
            level_image = Image.open(pic_path)
            made_rules = parse_statefunction(rule_name, level_image, r_dict)
            for r in made_rules:
                rules[r.name] = r
    if rules_yaml["Chains"] is not None:
        for c_dict in rules_yaml["Chains"]:
            rule = make_rule_chain(c_dict, rules)
            rules[rule.name] = rule
    if rules_yaml["Tests"] is not None:
        for t_dict in rules_yaml["Tests"]:
            test_name = list(t_dict.keys())[0]
            print("Test: {}".format(test_name))
            test_definition = t_dict[test_name]
            if test_definition is None:
                test_definition = {}
            t_dict = add_defaults(test_definition)
            pic_path = rules_path / (test_name + ".png")
            level_image = Image.open(pic_path)
            test = make_test_state(level_image, t_dict)
            tests[test_name] = test
    return rules, tests
