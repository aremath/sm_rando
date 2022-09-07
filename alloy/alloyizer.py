from functools import reduce
from encoding.parse_rooms import parse_rooms
from data_types import constraintgraph

i_type = "ItemNode"
d_type = "DoorNode"
door_tl = {"L": "Left",
        "T": "Up",
        # Bottom = Down
        "B": "Down",
        "R": "Right",
        "ET": "Down_Elevator",
        "EB": "Up_Elevator",
        "TS": "Down_Sand",
        "BS": "Up_Sand",
        "RMB": "Right_Morph",
        "LMB": "Left_Morph"
        }

# Omitted entries are treated as themselves
item_tl = {
        "B": "Bombs",
        "PB": "Power_Bombs",
        "SPB": "Spring_Ball",
        "S" : "Super_Missiles",
        "M" : "Missiles",
        "SA": "Screw_Attack",
        "G" : "Grapple_Beam",
        "V" : "Varia_Suiti",
        "GS" : "Gravity_Suit",
        "SB" : "Speed_Booster",
        "HJ" : "Hi_Jump",
        "MB" : "Morph",
        "CB" : "Charge_Beam",
        "WB" : "Wave_Beam",
        "E" : "Energy_Tank",
        "PLB" : "Plasma_Beam",
        "IB" : "Ice_Beam",
        "SJ" : "Space_Jump",
        "RT" : "Reserve_Tank",
        "XR" : "XRayi",
        "Spazer": "Spazeri",
        "Kraid" : "Kraidi",
        "Ridley" : "Ridleyi",
        "Phantoon": "Phantooni",
        "Mother_Brain": "Mother_Braini",
        "Spore_Spawn": "Spore_Spawni",
        "Botwoon" : "Botwooni",
        "Crocomire" : "Crocomirei",
        "Golden_Torizo": "Golden_Torizoi",
        "Drain": "Draini",
        "Shaktool": "Shaktooli",
        "Statues": "Statuesi",
        }

def mk_iset_str(itemset):
    item_set_conditions = []
    for item in itemset:
        if item in item_tl:
            i_str = item_tl[item]
        else:
            i_str = item
        cons_str = f"{i_str} in s.iset"
        item_set_conditions.append(cons_str)
    iset_str = "(" + " and ".join(item_set_conditions) + ")"
    return iset_str

def mk_minsetset_str(minsetset):
    # Translate the minsetset, which is in disjunctive normal form
    iset_strs = []
    for iset in minsetset:
        iset_str = mk_iset_str(iset)
        iset_strs.append(iset_str)
    item_str = "(" + " or ".join(iset_strs) + ")"
    return item_str

def alloyize(room, room_id):
    item_nodes = set(room.item_nodes)
    door_nodes = set(reduce(lambda x,y: x + y, [room.doors[d] for d in room.doors]))
    node_defs = []
    for node in room.graph.name_node:
        d = room.graph.name_node[node].data
        if isinstance(d, constraintgraph.Item) or isinstance(d, constraintgraph.Boss):
            type_str = i_type
            inner_str = f"room_id = {room_id}"
        if isinstance(d, constraintgraph.Door):
            type_str = d_type
            d = room.graph.name_node[node].data.facing
            d_str = door_tl[d]
            inner_str = f"direction = {d_str} room_id = {room_id}"
        node_def = f"one sig {node} extends {type_str} {{}} {{ {inner_str} }}"
        node_defs.append(node_def)
    factlines = []
    # Add constraints for each edge
    for node in room.graph.name_node:
        for edge in room.graph.node_edges[node]:
            item_str = mk_minsetset_str(edge.items.sets)
            # No need to create empty constraints
            # Kind of a hacky way to do this, but an empty minsetset consists of a single empty itemset for reasons
            if item_str == "(())":
                continue
            factline = f"\t\t(s'.loc = {node} and s.loc = {edge.terminal}) => {item_str}"
            factlines.append(factline)
    # Add custom constraints for door-based restrictions
    for node in room.graph.name_node:
        data = room.graph.name_node[node].data
        if isinstance(data, constraintgraph.Door):
            # Special case for grey doors
            if data.items is None:
                factline = f"\t\ts.loc.room_id = {room_id} => s'.loc != {node}"
            else:
                item_str = mk_minsetset_str(data.items.sets)
                if item_str == "(())":
                    continue
                factline = f"\t\t(s'.loc = {node}) and s.loc.room_id = {room_id} => {item_str}"
            factlines.append(factline)
    # Facts not dependent on state
    outer_factlines = []
    # Add custom constraints for boss nodes
    for node in room.graph.name_node:
        data = room.graph.name_node[node].data
        if isinstance(data, constraintgraph.Boss):
            boss_name = data.type
            # Must map the node to the correct boss
            f1 = f"World.items[{node}] = {boss_name}"
            # Cannot map any other nodes to that boss
            f2 = f"all i: ItemNode {{ i != {node} => World.items[i] != {boss_name} }}"
            outer_factlines.append(f1)
            outer_factlines.append(f2)
    fact_prefix = "fact {\n"
    fact_inner_prefix = "\tall s: State, s': s.next {\n"
    fact_inner_suffix = "\n\t}\n"
    facts_inner = fact_inner_prefix + "\n".join(factlines) + fact_inner_suffix
    facts_outer = "\n".join(outer_factlines)
    fact_suffix = "\n}\n"
    if len(factlines) == 0 and len(outer_factlines) == 0:
        fact_str = ""
    elif len(factlines) == 0:
        fact_str = fact_prefix + facts_outer + fact_suffix
    else:
        fact_str = fact_prefix + facts_inner + facts_outer + fact_suffix
    output = "\n".join(node_defs) + "\n" + fact_str
    return output

def get_item_name(item):
    if item in item_tl:
        i_str = item_tl[item]
    else:
        i_str = item
    return i_str

def mk_iset_str2(itemset):
    inames = [get_item_name(item) for item in itemset]
    return " + ".join(inames)

def alloyize2(room, exits):
    # Room def
    room_def = f"one sig {room.name} extends Room {{}}"
    # Node defs
    node_defs = []
    for node in room.graph.name_node:
        d = room.graph.name_node[node].data
        if isinstance(d, constraintgraph.Item) or isinstance(d, constraintgraph.Boss):
            type_str = "Drop"
            item = get_item_name(d.type)
            inner_str = f"room = {room.name} item = {item}"
        elif isinstance(d, constraintgraph.Door):
            type_str = "Door"
            partner = exits[node]
            inner_str = f"room = {room.name} partner = {partner}"
        node_def = f"one sig {node} extends {type_str} {{}} {{ {inner_str} }}"
        node_defs.append(node_def)
    # Link defs
    link_defs = []
    for node in room.graph.name_node:
        for edge in room.graph.node_edges[node]:
            mss = edge.items
            terminal = edge.terminal
            t_d = room.graph.name_node[terminal].data
            # Inaccessible door
            if isinstance(t_d, constraintgraph.Door) and t_d.items is None:
                continue
            # Push the door item constraint into the accessibility constraints
            elif isinstance(t_d, constraintgraph.Door):
                mss = mss * t_d.items
            # Make a Link for each possible path
            for i, iset in enumerate(mss.sets):
                iset_str = mk_iset_str2(iset)
                linkname = f"{node}_{terminal}_{i}"
                if iset_str == "":
                    iset_str = "none"
                link_def = f"one sig {linkname} extends Link {{}} {{ src = {node} dst = {terminal} requirements = {iset_str} }}"
                link_defs.append(link_def)
    all_defs = [room_def] + node_defs + link_defs
    return "\n".join(all_defs)

def alloyize_all(rooms):
    all_strs = []
    for i, (name, room) in enumerate(rooms.items()):
        #print(name)
        s = alloyize(room, i)
        all_strs.append(s)
    #all_strs = [alloyize(room, i) for i, (name, room) in enumerate(rooms.items())]
    return "\n".join(all_strs)

def alloyize_all2(rooms, exits):
    all_strs = []
    for i, (name, room) in enumerate(rooms.items()):
        #print(name)
        s = alloyize2(room, exits)
        all_strs.append(s)
    #all_strs = [alloyize(room, i) for i, (name, room) in enumerate(rooms.items())]
    return "\n\n".join(all_strs)
