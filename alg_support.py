
from parse_rooms import *
import collections

def make_door(door1, direction1, door2, direction2, new_room, graph, exits_to_place, door_changes, item_changes, items_to_place):
    """Connects door1 and door2, and updates all the accessories. Door1 is an already-placed door, and door2 is a door in new_room."""
    assert door_hookups[direction1] == direction2, door1 + " <-> " + door2

    # update exits_to_place
    # first, add all the exits from the new room
    for direction, doors in new_room[1].items():
            exits_to_place[direction].extend(doors)
    # now, remove the two doors that we placed
    exits_to_place[direction1].remove(door1)
    exits_to_place[direction2].remove(door2)

    # update door_changes
    door_changes.append((door1, door2))

    # update item_changes
    for item_node in new_room[2]:
        item = items_to_place.pop()
        new_room[0].graph.name_node[item_node].data.type = item
        item_changes.append((item_node, item))

    graph.add_room(door1, door2, new_room[0].graph)

def connect_doors(door1, direction1, door2, direction2, graph, exits_to_place, door_changes):
    """Connnects door1 and door2, and updates all accessories. the rooms that contain doors 1 and 2 have already been placed."""
    # make sure the doors actually hook up
    assert door_hookups[direction1] == direction2, door1 + " <-> " + door2
    # we're placing these exits, so we can remove them from exits_to_place
    exits_to_place[direction1].remove(door1)
    exits_to_place[direction2].remove(door2)
    # put this door connection in the connection list
    door_changes.append((door1, door2))

    # make the necessary changes to the graph
    door1_data = graph.name_node[door1].data
    door2_data = graph.name_node[door2].data
    # none means an impassable door
    if door1_data.items is not None:
        graph.add_edge(door1, door2, door1_data.items)
    if door2_data.items is not None:
        graph.add_edge(door2, door1, door2_data.items)

def dummy_exit_graph(graph, exits):
    dummy_exits = []
    dummy_graph = graph.copy()
    for direction_list in exits.values():
        for node in direction_list:
            # if it's possible to go through the door
            if graph.name_node[node].data.items is not None:
                node_constraint = graph.name_node[node].data.items
                dummy_name = node + "dummy"
                dummy_graph.add_node(dummy_name)
                dummy_graph.add_edge(node, dummy_name, node_constraint)
                dummy_exits.append(dummy_name)
    return dummy_graph, dummy_exits

# note that dummy exits are "traps" - there's no path back to node L from Ldummy.
def add_dummy_exits(graph, exits):
    added_nodes = []
    for direction in exits:
        for node in exits[direction]:
            print direction
            print node
            # if it's possible to go through the door
            if graph.name_node[node].data.accessible:
                node_constraint = graph.name_node[node].data.items
                dummy_name = node + "dummy"
                graph.add_node(dummy_name)
                graph.add_edge(node, dummy_name, node_constraint)
                added_nodes.append(node + "dummy")
    return added_nodes

def remove_dummy_exits(graph, exits):
    for direction in exits:
        for node in direction:
            if node + "dummy" in graph.name_node:
                graph.remove_node(node + "dummy")

def check_finished(finished_node, finished_entry, current_node, current_wildcards, current_items, room_exits):
    """Checks an entry of finished for whether it's an interesting 'path-through'
    That is, a path to a passable exit that either is different from current_node, or 
    goes to current_node's exit but picked up some items or something."""
    current_dummy = current_node + "dummy"
    # every path-through is to an exit!
    if finished_node in room_exits:
        # we made it through a different door
        if finished_node != current_dummy:
            return True
        # or we went back through the same door, but picked up an item or wildcard - just converting a wildcard to an item isn't sufficient
        if len(finished_entry[0]) + len(finished_entry[1]) > len(current_wildcards) + len(current_items):
            return True
    return False

def filter_paths(paths_through, current_node, current_wildcards, current_items, room_exits):
    for node, pt in paths_through.items():
        if len(pt) == 0:
            del paths_through[node]
        else:
            paths_through[node] = filter(lambda x: check_finished(node, x, current_node, current_wildcards, current_items, room_exits), pt)
    # now remove keys that don't have an interesting path-through
    for node, pt in paths_through.items():
        if len(pt) == 0:
            del paths_through[node]


def clean_rooms(rooms):
    """remove some rooms we don't want to change from the dictionary of rooms"""
    #TODO: this doesn't quite work... poping a room means I don't want to randomize any of its doors

    # get rid of pants_right - we're not using it: the cases in rom_edit will handle this.
    rooms.pop("Pants_Right")
    # don't randomize Ceres
    rooms.pop("Ceres_Entrance")
    rooms.pop("Ceres_1")
    rooms.pop("Ceres_2")
    rooms.pop("Ceres_3")
    rooms.pop("Ceres_4")
    rooms.pop("Ceres_Ridley")
    # don't randomize tourian or escape
    rooms.pop("Tourian_Elevator")
    rooms.pop("Metroid_Can_He_Crawl?")
    rooms.pop("Metroid_The_Return_of_Samus")
    rooms.pop("Metroid_Fusion?")
    rooms.pop("Metroid_Zero_Mission")
    rooms.pop("Blue_Hoppers")
    rooms.pop("RIP_Torizo")
    rooms.pop("Metroid_Skip")
    rooms.pop("Seaweed_Room")
    rooms.pop("Tourian_Refill")
    rooms.pop("Mother_Brain")
    rooms.pop("Tourian_Eye_Door")
    rooms.pop("Rinka_Shaft")
    rooms.pop("Mother_Brain_Save")
    rooms.pop("Escape_1")
    rooms.pop("Escape_2")
    rooms.pop("Escape_3")
    rooms.pop("Tourian_Save")
    #TODO - until I figure out what's wrong there...
    rooms.pop("Zip_Tube")

    #TODO: this doesn't quite work either - the resulting graph is messed up!
    # doesn't matter for the Pants room, but doesn't allow travel through escape, for example...

    # don't randomize Statues_ET
    rooms["Statues"][1]["ET"].remove("Statues_ET")
    # don't randomize Escape_4_L
    rooms["Escape_4"][1]["L"].remove("Escape_4_L")
    # don't randomize Pants_R2 or Pants_L2
    rooms["Pants"][1]["R"].remove("Pants_R2")
    rooms["Pants"][1]["L"].remove("Pants_L2")

def check_door_totals(rooms):
    """checks door totals - make sure the number of left doors is equal to the number of right doors etc."""
    door_totals = collections.Counter()
    # check the total number of doors:
    for room in rooms.values():
        room_doors = room[1]
        for direction, dir_doors in room_doors.items():
            door_totals[direction] += len(dir_doors)
    for door, partner in door_hookups.items():
        assert door_totals[door] == door_totals[partner], door + ": " + str(door_totals[door]) + ", " + partner + ": " + str(door_totals[partner])

def map_items():
    """get the items for the map - default behavior is just the normal numbers"""
    items_to_place = item_types + 45 * ["M"] + 9 * ["S"] + 9 * ["S"] + 13 * ["E"] + 2 * ["RT"]
    # stupid special cases
    items_to_place.remove("Bombs")
    items_to_place.append("B")
    return items_to_place

def get_fixed_items():
    """get the set of items whose locations cannot be changed"""
    return set(boss_types) | set(special_types)

def door_direction(door_name):
    """get the direction letter for a door node"""
    return door_name.split("_")[-1].rstrip("0123456789")

def check_backtrack(graph, current_node, backtrack_node, dummy_exits, current_wildcards, current_items, current_assignments, fixed_items):
    #print "backtracking to: " + backtrack_exit
    # pretend like they are connected - remove their dummy nodes from the list of dummies...
    # make a shallow copy first - if it turns out that backtracking was a bad decision, we need the original
    dummy_copy = dummy_exits[:]
    if current_node + "dummy" in dummy_copy:
            dummy_copy.remove(current_node + "dummy")
    if backtrack_node + "dummy" in dummy_copy:
            dummy_copy.remove(backtrack_+ "dummy")
    # and put edges between them
    current_node_constraints = current_graph.name_node[current_node].data.items
    backtrack_node_constraints = current_graph.name_node[backtrack_exit].data.items
    if current_node_constraints is not None:
            graph.add_edge(current_node, backtrack_node, current_node_constraints)
    if backtrack_node_constraints is not None:
            graph.add_edge(backtrack_node, current_node, backtrack_node_constraints)
    # find the reachable exits under the new scheme (start from current node, to ensure you can get to backtrack exit)
    backtrack_finished, _, _ = current_graph.BFS_items(current_node, None, current_wildcards, current_items, current_assignments, fixed_items)
    backtrack_exits = {exit: backtrack_finished[exit] for exit in dummy_copy if len(bfs_finished[exit]) != 0}
    # remove the edges we added
    if graph.is_edge(current_node, backtrack_node):
        graph.remove_edge(current_node, backtrack_node)
    if graph.is_edge(backtrack_node, current_node):
        graph.remove_edge(backtrack_node, current_node)
    return backtrack_exits, dummy_copy

