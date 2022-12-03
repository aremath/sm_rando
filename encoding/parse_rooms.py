# Author - Aremath
# parses the level file - in this repo, encoding/rooms.txt - see rooms.txt for more information on level encodings
# Basic Syntax: a room definition is as follows:
# title line:
# ROOM_NAME - ROOM_ADDRESS
# node definition:
# NODE_NAME - NODE_CONSTRAINTS (if any)
# edge_definition:
# (LIST_OF_NODES) -> (LIST_OF_NODES) - EDGE_CONSTRAINTS
# an edge definition can also use '<->' to denote edges in both directions.
# A ROOM is a title line, followed by any number of node and edge definitions.

# DOOR TYPES:
# (L R B T ET EB TS BS LMB RMB)

import collections

from encoding.constraints import *
from data_types.constraintgraph import *
from encoding import sm_global

def make_room(room_defn, library):
    # room defn is a list of strings, which are the lines of this room definition
    room_name, room_address = room_defn[0].split(" - ")
    graph = ConstraintGraph()
    room_nodes = []

    # key - door direction
    # value - list of door nodes in that direction
    door_dict = collections.defaultdict(list)

    item_nodes = []

    # TODO: make sure all the node definitions come before the edge constraints!
    node_lines = []
    edge_lines = []
    all_nodes = []
    for line in room_defn[1:]:
        parsed_line = parse_line(line, library, all_nodes)
        if parsed_line[0]:
            all_nodes.append(parsed_line[1][0])
            node_lines.append(parsed_line[1])
        else:
            edge_lines.append(parsed_line[1])

    # make a node for each node line
    for name, constraint in node_lines:
        node_data = parse_node_name(name, constraint)
        node_name = graph.add_node(room_name + "_" + name, node_data)
        room_nodes.append(node_name)
        if isinstance(node_data, Door):
            door_dict[node_data.facing].append(node_name)
        if isinstance(node_data, Item):
            item_nodes.append(node_name)

    # make it a complete graph
    for origin_node_name in room_nodes:
        for destination_node_name in room_nodes:
            if origin_node_name != destination_node_name:
                graph.add_edge(origin_node_name, destination_node_name)

    # add in the edge constraints
    scheduled_for_destruction = []
    for edges, constraint in edge_lines:
        if constraint is None:
            for edge in edges:
                scheduled_for_destruction.append(edge)
        else:
            for node1, node2 in edges:
                graph.add_edge(room_name + "_" + node1, room_name + "_" + node2, constraint)

    # remove "scheduled_for_destruction" edges
    # first, get rid of duplicates.
    scheduled_for_destruction = list(set(scheduled_for_destruction))

    for node1, node2 in scheduled_for_destruction:
        graph.remove_edge(room_name + "_" + node1, room_name + "_" + node2)

    room = Room(room_name, int(room_address, 16), graph, door_dict, item_nodes)
    return room

def parse_line(line, library, all_nodes=[]):
    """Categorizes and parses an item definition or edge definition line. The syntax is above"""
    # edge lines have "->" present ALWAYS
    edge_line = line.split("->")
    assert len(edge_line) <= 2, "TOO MANY ARROWS: " + line
    if len(edge_line) == 1:
        return (True, parse_node_line(line, library))
    elif len(edge_line) == 2:
        return (False, parse_edge_line(line, all_nodes, library))

def parse_node_line(line, library):
    """Helper function for parse_line - returns a tuple of node_name, constraint_set."""
    name = ""
    constraint = MinSetSet()

    split = line.split("-")
    assert len(split) <= 2, "TOO MANY DASHES: " + line
    name = split[0].strip()
    assert len(name) != 0, "WHITESPACE NAME: " + line
    if len(split) == 2:
        str_constraint = split[1].strip()
        if str_constraint == "X":
            constraint = None
        else:
            constraint = parse_constraint(str_constraint)

    return name, constraint

def parse_edge_line(line, all_nodes, library):
    """Helper function for parse_line - returns a tuple of (all affected edges), constraint_set."""
    back = False
    left, right = line.split("->")
    # also reverse?
    if left[-1] == "<":
        back = True
        left = left[:-1]
    # now, break off the constraint
    right, str_constraint = right.split("-")
    # parse left and right
    # first, remove unnecessary spaces
    left = left.strip()
    # it's a set of nodes; remove the parens, then make a list
    if left[0] == "(":
        left = left[1:-1].split()
    # it's all nodes; use our definition for all
    elif left == "ALL":
        left = all_nodes
    # it's a single node; make a list
    else:
        left = [left]

    right = right.strip()
    if right[0] == "(":
        right = right[1:-1].split()
    elif right == "ALL":
        right = all_nodes
    else:
        right = [right]
    str_constraint = str_constraint.strip()

    # now make the node pairs that represent edges
    edges = []
    for left_node in left:
        for right_node in right:
            # nodes shouldn't have edges to themselves...
            if left_node != right_node:
                edges.append((left_node, right_node))
                if back:
                    edges.append((right_node, left_node))

    if str_constraint == "X":
        constraint = None
    else:
        constraint = parse_constraint(str_constraint, library)
    return edges, constraint

def parse_node_name(node_name, constraint):
    """Helper function for make_room. categorizes a node name, returning an
    Item, a Door, or a Boss"""
    # TODO: parse a memory addresses file to get the address
    # get the type by stripping the number from the end
    node_type = node_name.rstrip("1234567890")

    if node_type in sm_global.door_types:
        accessible = True
        if constraint is None:
            accessible = False
        return Door(0, constraint, accessible, node_type)
    elif node_type in sm_global.item_types:
        # quick and dirty fix. Otherwise the bombs thing would be parsed as a bottom exit
        # and not an item node.
        if node_type == "Bombs":
            return Item(0, "B")
        return Item(0, node_type)
    # Special nodes act as bosses - they're the same in that they can't be
    # randomized
    elif node_type in sm_global.boss_types or node_type in sm_global.special_types:
        return Boss(node_type)
    # Allow for semantic nodes that do not have node data
    else:
        return None

def parse_constraintdef(line, library):
    l, r = line.split("=")
    l = l.strip()
    r = r.strip()
    c = parse_constraint(r, library)
    return l, c

def parse_rooms(room_file):
    # open the file
    f = open(room_file, "r")
    # For holding constraint definitions
    current_library = default_library
    # Parse each room definition
    # Key - room name
    # Value - room graph and door dictionary
    rooms = {}
    current_room = []
    # Read the lines to create the room definitions
    for line in f.readlines():
        # remove unnecessary characters
        line = line.strip()
        # Blank line means new room
        if len(line) == 0 and len(current_room) >= 1:
            room = make_room(current_room, current_library)
            rooms[room.name] = room
            current_room = []
        # Skip comments
        elif len(line) == 0 or line[0] == "#":
            continue
        elif "=" in line and len(current_room) == 0:
            name, constraint = parse_constraintdef(line, current_library)
            current_library[name] = constraint
        elif len(line) > 0:
            current_room.append(line)
    # Create the last room
    if len(current_room) >= 1:
        room = make_room(current_room, current_library)
        rooms[room.name] = room
    f.close()
    return rooms

def parse_exits(exits_file):
    out = {}
    with open(exits_file, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line[0] == "#":
                continue
            door_a, door_b = line.split("<>")
            door_a = door_a.strip()
            door_b = door_b.strip()
            out[door_a] = door_b
            out[door_b] = door_a
    return out

def dictify_rooms(rooms, exits):
    """
    Convert rooms to a dictionary object compatible with JSON
    (Use json.dumps to create a json string)
    """
    d_rooms = {room.name : room.dictify(exits) for room in rooms.values()}
    #TODO: Add Landing_Site_Ship (requires changing this file to allow non-item, non-door nodes
    out = {"Start": {"Node": "Landing_Site_L2", "Items": []},
            "End": {"Node": "Landing_Site_L2", "Items": ["Mother_Brain"]},
            "Items": {i: sm_global.item_translate[i] for i in sm_global.items + sm_global.special_types},
            "Bosses": {i: sm_global.item_translate[i] for i in sm_global.bosses + sm_global.minibosses},
            "Door_Directions": { d: {"Name": sm_global.door_translate[d], "Partner": sm_global.door_hookups[d]} for d in sm_global.door_types },
            "Rooms": d_rooms}
    return out
