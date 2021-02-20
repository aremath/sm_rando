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

from sm_rando.encoding.constraints import *
from sm_rando.data_types.constraintgraph import *
from sm_rando.encoding import sm_global

door_hookups = {
    "L": "R",
    "R": "L",
    "T": "B",
    "B": "T",
    "ET": "EB",
    "EB": "ET",
    "TS": "BS",
    "BS": "TS",
    "LMB": "RMB",
    "RMB": "LMB"
}

def make_room(room_defn):
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
        parsed_line = parse_line(line, all_nodes)
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

    room = Room(room_name, 0, graph, door_dict, item_nodes)
    return room

def parse_line(line, all_nodes=[]):
    """Categorizes and parses an item definition or edge definition line. The syntax is above"""
    # edge lines have "->" present ALWAYS
    edge_line = line.split("->")
    assert len(edge_line) <= 2, "TOO MANY ARROWS: " + line
    if len(edge_line) == 1:
        return (True, parse_node_line(line))
    elif len(edge_line) == 2:
        return (False, parse_edge_line(line, all_nodes))

def parse_node_line(line):
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

def parse_edge_line(line, all_nodes):
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
        constraint = parse_constraint(str_constraint)
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
    else:
        assert False, "Unrecognized Type: " + node_name


def parse_rooms(room_file):
    # open the file
    f = open(room_file, "r")
    # read the lines to create the room definitions
    room_defs = []
    current_room = []
    for line in f.readlines():
        # remove unnecessary characters
        line = line.strip()
        # blank line means new room
        if len(line) == 0:
            room_defs.append(current_room)
            current_room = []
        # skip comments
        elif line[0] == "#":
            continue
        else:
            current_room.append(line)
    # append the last room
    room_defs.append(current_room)

    # parse each room definition
    # key - room name
    # value - room graph and door dictionary
    rooms = {}
    for room_def in room_defs:
        # if we got a room without any data somehow, chuck it
        if len(room_def) >= 1:
            room = make_room(room_def)
            rooms[room.name] = room
    f.close()
    return rooms
