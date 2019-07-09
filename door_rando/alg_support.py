from encoding import sm_global
from encoding.parse_rooms import *
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

#TODO have this take just a room, now that rooms have .doors?
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
            print(direction)
            print(node)
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

#TODO: we don't need this anymore?
def check_finished(finished_node, finished_items, finished_entry, state, room_exits):
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
        if finished_items > state.items or len(finished_entry[0]) > len(state.wildcards):
            return True
    return False

# paths-through is a finished BFS_items result, which means it has
# key - node
# key - item set
# value - (wildcards, assignments) list
"""
def filter_paths(paths_through, state, room_exits):
    ""Updates a paths-through to only those paths which reach exits and make some kind of progress""
    # will be a filtered copy of paths
    new_paths = collections.defaultdict(lambda: collections.defaultdict(list))
    for node, idc in paths_through.items():
        # we don't care about nodes that aren't exits
        if node not in room_exits:
            break
        # otherwise, it's a dict with key - item, value - wildcards list
        for items, wilds in idc.items():
            # we don't care about items with an empty reachable set #TODO: this can't/shouldn't happen?
            if len(wilds) == 0:
                break
            for wild in wilds:
                # if the state made up by the finished entry is valid, add it to the new paths
                if state.is_progress(BFSItemsState(node, wild[0], items, wild[1])):
                    new_paths[node][items] = wild
    paths_through = new_paths
"""

# slightly less efficient than ^, but also much easier to read
#TODO: Hacky
def filter_paths(paths_through, state, room_exits):
    
    def is_path(other_state):
        if other_state.node not in room_exits:
            return False
        elif state.is_progress(other_state):
            if other_state.node == state.node + "dummy":
                return ((other_state.items > state.items) or (len(other_state.wildcards) > len(state.wildcards)))
            else:
                return True
        else:
            return False

    return filter_finished(is_path, paths_through)

def to_states(items_finished):
    """takes a BFS_items result and converts it into a list of states"""
    states = []
    for node, idc in items_finished.items():
        for items, wilds in idc.items():
            for wild in wilds:
                states.append(BFSItemsState(node, wild[0], items, wild[1]))
    return states

def from_states(bfs_states):
    """takes a list of BFSItemsStates and converts it to a BFS_items result"""
    finished = collections.defaultdict(lambda: collections.defaultdict(list))
    for state in bfs_states:
        finished[state.node][state.items].append((state.wildcards, state.assignments))
    return finished

#TODO: filter the to_states list so that only pareto-maximal elements are kept ?
# - want to use states that keep wildcards instead of items
# - want to use states that pick up wildcards instead of leaving them
def filter_finished(pred, finished):
    """filters the bfs_items result to all states matching pred"""
    states = to_states(finished)
    states = filter(pred, states)
    return from_states(states)

def print_finished(finished):
    "prints a BFS_Items finished table"
    for node in finished:
        print(node)
        for iset in finished[node]:
            print("\t" + str(iset))
            for wildcards, assignments in finished[node][iset]:
                print("\t\t" + str(wildcards) + "\t" + str(assignments))

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
    rooms["Statues"].doors["ET"].remove("Statues_ET")
    # don't randomize Escape_4_L
    rooms["Escape_4"].doors["L"].remove("Escape_4_L")
    # don't randomize Pants_R2 or Pants_L2
    rooms["Pants"].doors["R"].remove("Pants_R2")
    rooms["Pants"].doors["L"].remove("Pants_L2")

def check_door_totals(rooms):
    """checks door totals - make sure the number of left doors is equal to the number of right doors etc."""
    door_totals = collections.Counter()
    # check the total number of doors:
    for room in rooms.values():
        for direction, dir_doors in room.doors.items():
            door_totals[direction] += len(dir_doors)
    for door, partner in door_hookups.items():
        assert door_totals[door] == door_totals[partner], door + ": " + str(door_totals[door]) + ", " + partner + ": " + str(door_totals[partner])

# old map_items()
"""
def map_items():
    items_to_place = item_types + 45 * ["M"] + 9 * ["S"] + 9 * ["PB"] + 13 * ["E"] + 2 * ["RT"]
    # stupid special cases
    items_to_place.remove("Bombs")
    items_to_place.append("B")
    return items_to_place
"""

def map_items():
    """get the items for the map - default behavior is just the normal numbers"""
    items_to_place = (2 * sm_global.items) + (22 * ["M"]) + (12 * ["S"]) + (10 * ["PB"]) + (14 * ["E"])
    assert len(items_to_place) == 100, len(items_to_place)
    # stupid special cases
    return items_to_place


def get_fixed_items():
    """get the set of items whose locations cannot be wildcarded"""
    return ItemSet(sm_global.boss_types) | ItemSet(sm_global.special_types)

def get_starting_assignments():
    """get the assignments to items whose locations which do not accept wildcards"""
    return {"Water_Closet_Drain" : "Drain", "Shaktool_Shaktool": "Shaktool"}

def door_direction(door_name):
    """get the direction letter for a door node"""
    return door_name.split("_")[-1].rstrip("0123456789")

def check_backtrack(graph, current_state, backtrack_node, dummy_exits, fixed_items):
    #print "backtracking to: " + backtrack_node
    # pretend like they are connected - remove their dummy nodes from the list of dummies...
    # make a shallow copy first - if it turns out that backtracking was a bad decision, we need the original
    dummy_copy = dummy_exits[:]
    if current_state.node + "dummy" in dummy_copy:
            dummy_copy.remove(current_state.node + "dummy")
    if backtrack_node + "dummy" in dummy_copy:
            dummy_copy.remove(backtrack_node + "dummy")
    # and put edges between them via an intermediate
    # TODO: removing a node is slow, but doesn't wreck the graph
    intermediate = current_state.node + "_int_" + backtrack_node
    graph.add_node(intermediate)
    current_node_constraints = graph.name_node[current_state.node].data.items
    backtrack_node_constraints = graph.name_node[backtrack_node].data.items
    if current_node_constraints is not None:
            graph.add_edge(current_state.node, intermediate, current_node_constraints)
            graph.add_edge(intermediate, backtrack_node)
    if backtrack_node_constraints is not None:
            graph.add_edge(backtrack_node, intermediate, backtrack_node_constraints)
            graph.add_edge(intermediate, current_state.node)
    # find the reachable exits under the new scheme (start from current node, to ensure you can get to backtrack exit)
    backtrack_finished, _, _ = graph.BFS_items(current_state, fixed_items=fixed_items)
    backtrack_exits = {exit: backtrack_finished[exit] for exit in dummy_copy if len(backtrack_finished[exit]) != 0}
    # return the intermediate so that the alg can remove it if this backtrack wasn't used
    return backtrack_exits, dummy_copy, intermediate

