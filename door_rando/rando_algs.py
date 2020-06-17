import random
import itertools
from functools import reduce

from sm_rando.misc.progress_bar import print_progress_bar
from sm_rando.door_rando.alg_support import *
from sm_rando.data_types.graph import BFSItemsState, bfs_items_backtrack

#TODO: Room Orientation randomization???? (far future)
#TODO: This doesn't always take the "right" path-through. For example,
# with Hopper_Energy, there are two paths from L. L, and L -> E -> L.
# if L -> E -> L isn't taken, we don't wind up with the item like usual.
# also with Alpha_Power_Bombs

#TODO: implement grey doors as an "impossible" item rather than as no edges?
# potentially slightly slower, but also many fewer "check if there's an edge" cases
# and no "check if there's a dummy exit" cases

#TODO: figure out where / why this is getting stuck

# New idea - give the player some items, then just randomly place the rest of the map
def item_quota_rando(rooms, debug, starting_items, items_to_place):
    # INITIALIZATION:
    clean_rooms(rooms)
    check_door_totals(rooms)
    nrooms = len(rooms)
    nrooms_placed = 0
    statues_state = None
    progress_prefix = "Placing Rooms:"
    # Start at landing site
    landing_site = rooms.pop("Landing_Site")
    current_graph = landing_site.graph
    #TODO: copy?
    # Keeps track of all extant doors
    exits_to_connect = landing_site.doors
    # Keeps track of the current BFS state
    current_state = BFSItemsState("Landing_Site_R2", items_=starting_items)
    current_state.assignments = get_starting_assignments()
    # Keeps track of exits reachable from current node
    reachable_exits = []
    # Get a random order for items to place 
    random.shuffle(items_to_place)
    # Get the list of items which have fixed locations (bosses, etc.)
    fixed_items = get_fixed_items()
    # Get a random order for rooms
    rooms_to_place = list(rooms.keys())
    random.shuffle(rooms_to_place)
    # Initialize changes
    door_changes = []
    item_changes = []
    # Keeps track of placed but not assigned item nodes
    unassigned_item_nodes = []
    #
    path = []
    # make dummy exit nodes for landing_site
    # these dummy exits serve to let the BFS search not just reachable doors, but enterable doors.
    current_graph, dummy_exits = dummy_exit_graph(current_graph, exits_to_connect)

    if not debug:
        print_progress_bar(nrooms_placed, nrooms, prefix=progress_prefix)

    #TODO: maybe doing this places too many items too early?
    while len(rooms_to_place) > 0:
        # To record the current state and remember the path
        start_state = current_state.copy()
        # Wildcard BFS to find reachable exits
        o, bfs_finished, _, _ = current_graph.BFS_items(current_state, None, fixed_items)
        reachable_exits = [s for s in bfs_finished if s.node in dummy_exits]
        #print(reachable_exits)

        #TODO: Consider multiple backtracks?
        # CONSIDER BACKTRACKING:
        # If there are more reachable exits by backtracking, do so!
        # Choose a random extant door that this door can hook up with
        current_direction = door_direction(current_state.node)
        # If we haven't already connected the current exit and if there is a valid backtracking exit
        if current_state.node in exits_to_connect[current_direction] and len(exits_to_connect[door_hookups[current_direction]]) > 0:
            backtrack_exit = random.choice(exits_to_connect[door_hookups[current_direction]])
            backtrack_o, backtrack_finished, dummy_copy, intermediate = check_backtrack(current_graph, current_state, backtrack_exit, dummy_exits, fixed_items)

            #TODO: greater than or equal to?
            #TODO: how much of this should be in check_backtracks? technically all of this could be moved
            # If there are more reachable exits by backtracking, do so!
            if len(backtrack_finished) > len(reachable_exits):
                # Those dummy exits aren't there anymore
                # Remove the actual dummy exits from the graph
                if current_state.node + "dummy" in dummy_exits:
                    current_graph.remove_node(current_state.node + "dummy")
                if backtrack_exit + "dummy" in dummy_exits:
                    current_graph.remove_node(backtrack_exit + "dummy")
                # The copied dummy already has those exits removed.
                dummy_exits = dummy_copy
                # We no longer have to connect them
                exits_to_connect[current_direction].remove(current_state.node)
                exits_to_connect[door_hookups[current_direction]].remove(backtrack_exit)
                # Update door changes
                door_changes.append((current_state.node, backtrack_exit))
                # Set reachable exits we got from backtracking
                reachable_exits = backtrack_finished
                o = backtrack_o
                if debug:
                    print("\tBacktrack connecting {} to {}".format(current_state.node, backtrack_exit))
            # Otherwise, repair the damage to the graph and keep going
            else:
                current_graph.remove_node(intermediate)

        if len(reachable_exits) == 0:
            # if there aren't any reachable exits, place the rest of the rooms at random - hopefully there's a path to statues :)
            if debug:
                print("No reachable exits")
            break
            #assert False, "No reachable exits: \n" + str(door_changes) + "\n" + str(current_assignments)
        
        exit_states = reachable_exits
        random.shuffle(exit_states)
        found = False
        # Keep trying until we exhaust the list of exit states too
        # LOOP over exit states, trying to place a room at one of them
        for exit_state in exit_states:
            if found:
                break
            chosen_exit = exit_state.node
            # Update with the choices we made to use that path
            chosen_direction = door_direction(chosen_exit[:-5])

            # Find a room with a path-through
            # Shuffle them to eliminate the extra work of getting re-testing of bad rooms
            random.shuffle(rooms_to_place)
            # LOOP over rooms trying to place each one at the chosen exit state
            for room_name in rooms_to_place:
                if found:
                    break
                room = rooms[room_name]
                # Add dummy exit nodes
                room_graph, room_dummy_exits = dummy_exit_graph(room.graph, room.doors)
                room_direction = door_hookups[chosen_direction]
                # Find an entrance that matches - TODO - for loop - all entrances that match
                if len(room.doors[room_direction]) == 0:
                    continue
                if room_name == "Statues" and debug:
                    print("Considering Statues")
                    print(exit_state)
                chosen_entrance = random.choice(room.doors[room_direction])
                #TODO: where to start the BFS?
                entrance_state = BFSItemsState(chosen_entrance, exit_state.wildcards, exit_state.items, exit_state.assignments)
                room_o, paths_through, _, _ = room_graph.BFS_items(entrance_state, None, fixed_items)
                paths_through = filter_paths(paths_through, entrance_state, room_dummy_exits)
                # If there is at least one path-through - take one. We are going to definitely place this room.
                if len(paths_through) > 0:
                    if debug:
                        print("Placing " + chosen_entrance + " at " + chosen_exit[:-5])
                        if chosen_entrance == "Statues_L":
                            print("PLACED STATUES")
                            statues_state = exit_state.copy()
                            statues_state.node = chosen_exit[:-5]
                    #print("PATHS: {}".format(paths_through))
                    # Pick a path-through to follow and update the current state.
                    current_state = random.choice(list(paths_through))
                    # Remove "dummy"
                    current_state.node = current_state.node[:-5]

                    # Connect the two rooms at chosen_exit , chosen_entrance
                    # For now, add every item node: we don't know which ones will end up being assigned.
                    unassigned_item_nodes.extend(room.item_nodes)

                    # Update dummy exits!
                    if chosen_entrance + "dummy" in room_dummy_exits:
                        room_graph.remove_node(chosen_entrance + "dummy")
                        room_dummy_exits.remove(chosen_entrance + "dummy")
                    if chosen_exit in dummy_exits:
                        current_graph.remove_node(chosen_exit)
                        dummy_exits.remove(chosen_exit)
                    chosen_exit = chosen_exit[:-5]
                    dummy_exits.extend(room_dummy_exits)

                    # Update exits_to_connect
                    # Add all the exits of the new room
                    # TODO: It would be nice to just add these two dicts together using a defined +
                    for direction, doors in room.doors.items():
                        exits_to_connect[direction].extend(doors)
                    # Now get rid of the two doors we just hooked up
                    exits_to_connect[chosen_direction].remove(chosen_exit)
                    exits_to_connect[room_direction].remove(chosen_entrance)

                    # Add the graph of the other room
                    current_graph.add_room(chosen_exit, chosen_entrance, room_graph)

                    door_changes.append((chosen_exit, chosen_entrance))
                    # The room has been placed
                    rooms_to_place.remove(room_name)
                    nrooms_placed += 1
                    if not debug:
                        print_progress_bar(nrooms_placed, nrooms, prefix=progress_prefix)
                    found = True
                    # The last element will always be a dummy node
                    path_to_room = bfs_items_backtrack(start_state, exit_state, o)[:-1]
                    n_path_to_room = [s.node for s in path_to_room]
                    path_in_room = bfs_items_backtrack(entrance_state, current_state, room_o)
                    n_path_in_room = [s.node for s in path_in_room]
                    local_path = n_path_to_room + n_path_in_room
                    # The local_paths always contain the same node at start and end
                    path += local_path[1:]
                    if debug:
                        print("\tUsing {}".format(local_path))

        # We're done with the loop over states and didn't find anything :(
        if not found:
            if debug:
                print("No states with a path-through")
            break
        #### End condition: all exit states and rooms have been exhausted

    # RANDOM PLACEMENT:
    unassigned_item_nodes = [node for node in unassigned_item_nodes if node not in current_state.assignments]
    item_changes.extend(current_state.assignments.items())
    # Make the current assignment a reality (in the graph)
    # TODO: with already-assigned nodes that haven't been placed yet?
    for node, item in current_state.assignments.items():
        if node in current_graph.name_node:
            current_graph.name_node[node].data.type = item
    # Place unassigned items
    #TODO: maybe do something more sophisticated to place progression items at reachable locations?
    # first, calculate the items that haven't been placed!
    for item in current_state.assignments.values():
        if item in items_to_place:
            items_to_place.remove(item)
    for item_node in unassigned_item_nodes:
        item = items_to_place.pop()
        current_graph.name_node[item_node].data.type = item
        item_changes.append((item_node, item))

    # Remove dummy exits
    for exit in dummy_exits:
        current_graph.remove_node(exit)

    # Now just place rooms randomly
    # While there are doors that haven't been connected
    while reduce(lambda x,y: x or y, [len(direction_doors) != 0 for direction_doors in exits_to_connect.values()]):

        # All directions that still have a door left to place
        directions_left = [direction for direction in exits_to_connect.keys() if len(exits_to_connect[direction]) != 0]

        # If there are no rooms left to place...
        if len(rooms_to_place) == 0:
            # Pick a random direction with doors left to place
            direction = random.choice(directions_left)
            other_direction = door_hookups[direction]
            door = random.choice(exits_to_connect[direction])
            other_door = random.choice(exits_to_connect[other_direction])
            # Update bookeeping
            exits_to_connect[direction].remove(door)
            exits_to_connect[other_direction].remove(other_door)
            door_changes.append((door, other_door))
            # Add that change to the graph
            door_data = current_graph.name_node[door].data
            other_door_data = current_graph.name_node[other_door].data
            # None indicates an impassable door
            if door_data.items is not None:
                current_graph.add_edge(door, other_door, door_data.items)
            if other_door_data.items is not None:
                current_graph.add_edge(other_door, door, other_door_data.items)

        # If there are still rooms left to place
        else:
            # Pick a room to place - try rooms until we can place one
            found = -1
            for index in range(len(rooms_to_place)):
                room_doors = rooms[rooms_to_place[index]].doors
                room_directions = list(room_doors.keys())
                random.shuffle(room_directions)
                for room_direction in room_directions:
                    # Pick a representative for each direction
                    if len(room_doors[room_direction]) == 0:
                        continue
                    direction_door = random.choice(room_doors[room_direction])
                    match_direction = door_hookups[room_direction]
                    # Find a match!
                    if len(exits_to_connect[match_direction]) != 0:
                        exit = random.choice(exits_to_connect[match_direction])
                        new_room = rooms[rooms_to_place[index]]
                        # Link the two exits
                        # Add every exit in the new room to the list of exits we must connect
                        for direction, doors in new_room.doors.items():
                            exits_to_connect[direction].extend(doors)
                        # Remove the two doors we just placed
                        exits_to_connect[room_direction].remove(direction_door)
                        exits_to_connect[match_direction].remove(exit)

                        door_changes.append((direction_door, exit))

                        # Update the graph
                        current_graph.add_room(exit, direction_door, new_room.graph)

                        # Add items, if necessary
                        for item_node in new_room.item_nodes:
                            item = items_to_place.pop()
                            current_graph.name_node[item_node].data.type = item
                            item_changes.append((item_node, item))

                        found = index
                        break
                if found >= 0:
                    break
            # We placed the room at index - remove it
            rooms_to_place.pop(found)
            nrooms_placed += 1
            if not debug:
                print_progress_bar(nrooms_placed, nrooms, prefix=progress_prefix)
        #print sum([len(dir_doors) for dir_doors in current_exits.values()])
    if debug:
        print("ROOMS NOT PLACED - " + str(len(rooms_to_place)))
    else:
        # Dirty hack to get it to finish...
        print_progress_bar(nrooms, nrooms, prefix=progress_prefix)
    # If statues was placed as a room with a path-through, then it will be more accurate
    # to search from this state rather than some later state which may be at a softlock location
    if statues_state is None:
        final_state = current_state
    else:
        final_state = statues_state
    return door_changes, item_changes, current_graph, final_state, path

def basic_rando(rooms):

    # remove rooms we're not randomizing
    clean_rooms(rooms)
    # do this after cleaning - pants room plays havoc with this since there's
    # two right doors that both lead to shaktool.
    check_door_totals(rooms)

    landing_site = rooms.pop("Landing_Site")
    current_graph = landing_site[0].graph
    current_exits = landing_site[1]

    # get a random order for items
    items_to_place = map_items()
    random.shuffle(items_to_place)

    # get a random order for rooms
    rooms_to_place = list(rooms.keys())
    random.shuffle(rooms_to_place)

    door_changes = []
    item_changes = []

    # while not all of the exits have been placed...
    #TODO: actually while we haven't placed all the rooms...
    while reduce(lambda x, y: x or y, [len(direction_doors) != 0 for direction_doors in current_exits.values()]):

        directions_left = [direction for direction in current_exits.keys() if len(current_exits[direction]) != 0]

        # if we're out of rooms to place...
        if len(rooms_to_place) == 0:
            # pick a random direction with doors still to place
            direction = random.choice(directions_left)
            door = random.choice(current_exits[direction])
            other_door = random.choice(current_exits[door_hookups[direction]])
            # TODO: add that change to the graph
            connect_doors(door, direction, other_door, door_hookups[direction], current_graph, current_exits, door_changes)

        # we're not out of rooms to place
        else:
            # pick a room to place - try rooms until we can place one
            found = -1
            for index in range(len(rooms_to_place)):
                room_doors = rooms[rooms_to_place[index]][1]
                room_directions = room_doors.keys()
                random.shuffle(room_directions)
                for room_direction in room_directions:
                    # pick a representative for each direction
                    if len(room_doors[room_direction]) == 0:
                        continue
                    direction_door = random.choice(room_doors[room_direction])
                    match_direction = door_hookups[room_direction]
                    # find a match!
                    if len(current_exits[match_direction]) != 0:
                        exit = random.choice(current_exits[match_direction])
                        # link the two exits - remove the two doors we linked
                        make_door(exit, match_direction, direction_door, room_direction,
                                  rooms[rooms_to_place[index]], current_graph, current_exits,
                                  door_changes, item_changes, items_to_place)
                        found = index
                        break
                if found >= 0:
                    break
            # we placed the room at index - remove it
            rooms_to_place.pop(found)
        #print sum([len(dir_doors) for dir_doors in current_exits.values()])
    print("ROOMS NOT PLACED - " + str(len(rooms_to_place)))
    # return the list of door and item changes
    return door_changes, item_changes, current_graph
