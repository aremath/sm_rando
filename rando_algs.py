
from alg_support import *
import random

#TODO: Room Orientation randomization???? (far future)
#TODO: This doesn't always take the "right" path-through. For example,
# with Hopper_Energy, there are two paths from L. L, and L -> E -> L.
# if L -> E -> L isn't taken, we don't wind up with the item like usual.
# also with Alpha_Power_Bombs

#TODO: implement grey doors as an "impossible" item rather than as no edges?
# potentially slightly slower, but also many fewer "check if there's an edge" cases
# and no "check if there's a dummy exit" cases

#TODO: figure out where / why this is getting stuck
#TODO: keep the state at the end to help with the final BFS
#TODO: see if the item quota idea actually works??

# new idea - give the player some items, then just randomly place the rest of the map
def item_quota_rando(rooms, starting_items=ItemSet()):
    clean_rooms(rooms)
    check_door_totals(rooms)

    landing_site = rooms.pop("Landing_Site")
    current_graph = landing_site.graph
    #TODO: copy?
    exits_to_connect = landing_site.doors

    # keeps track of the current BFS state
    current_state = BFSItemsState("Landing_Site_R2", items_=starting_items)
    current_state.assignments = get_starting_assignments()

    # keeps track of exits reachable from current node
    reachable_exits = []

    # get a random order for items - used after we have assigned all of the items required to pass statues
    items_to_place = map_items()
    random.shuffle(items_to_place)

    # get the list of items which have fixed locations (bosses, etc.)
    fixed_items = get_fixed_items()

    # get a random order for rooms
    rooms_to_place = rooms.keys()
    random.shuffle(rooms_to_place)

    door_changes = []
    item_changes = []

    # keeps track of placed but not assigned item nodes
    unassigned_item_nodes = []

    # make dummy exit nodes for landing_site
    # these dummy exits serve to let the BFS search not just reachable doors, but enterable doors.
    current_graph, dummy_exits = dummy_exit_graph(current_graph, exits_to_connect)

    #TODO: maybe doing this places too many items too early?
    while len(rooms_to_place) > 0:
        #print "At: " + str(current_state)
        # wildcard BFS to find reachable exits
        bfs_finished, _, _ = current_graph.BFS_items(current_state, None, fixed_items)
        #print_finished(bfs_finished)
        # dict comprehensions! - entries of bfs_finished that are dummy exits and actually have a path to them.
        reachable_exits = {exit: bfs_finished[exit] for exit in dummy_exits if len(bfs_finished[exit]) != 0}

        #TODO: might need to decide on a reachable exit first?
        #TODO: I think this works now... Consider multiple backtracks?
        # if there are more reachable exits by backtracking, do so!
        # choose a random (already-placed) door that this door can hook up with
        current_direction = door_direction(current_state.node)
        # if we haven't already connected the current exit and if there is a valid backtracking exit
        if current_state.node in exits_to_connect[current_direction] and len(exits_to_connect[door_hookups[current_direction]]) > 0:
            backtrack_exit = random.choice(exits_to_connect[door_hookups[current_direction]])
            backtrack_finished, dummy_copy, intermediate = check_backtrack(current_graph, current_state, backtrack_exit, dummy_exits, fixed_items)

            #print "at: " + current_state.node
            #print "try backtrack to: " + backtrack_exit
            #print "reaching: " + str(backtrack_finished.keys())
            #print "with no backtrack: " + str(reachable_exits.keys())

            #TODO: greater than or equal to?
            #TODO: how much of this should be in check_backtracks? technically all of this could be moved
            # if there are more reachable exits by backtracking, do so!
            if len(backtrack_finished.keys()) > len(reachable_exits.keys()):
                #print "BACKTRACKED!"
                # those dummy exits aren't there anymore
                # remove the actual dummy exits from the graph
                if current_state.node + "dummy" in dummy_exits:
                    current_graph.remove_node(current_state.node + "dummy")
                if backtrack_exit + "dummy" in dummy_exits:
                    current_graph.remove_node(backtrack_exit + "dummy")
                # the copied dummy already has those exits removed.
                dummy_exits = dummy_copy
                # we no longer have to connect them
                exits_to_connect[current_direction].remove(current_state.node)
                exits_to_connect[door_hookups[current_direction]].remove(backtrack_exit)
                # update door changes
                door_changes.append((current_state.node, backtrack_exit))
                # set reachable exits so that the next part works
                reachable_exits = backtrack_finished
            # otherwise, repair the damage to the graph and keep going
            else:
                current_graph.remove_node(intermediate)

        if len(reachable_exits.keys()) == 0:
            # if there aren't any reachable exits, place the rest of the rooms at random - hopefully there's a path to statues :)
            break
            #assert False, "No reachable exits: \n" + str(door_changes) + "\n" + str(current_assignments)
        
        exit_state = choose_random_state(reachable_exits)
        chosen_exit = exit_state.node
        # update with the choices we made to use that path
        chosen_direction = door_direction(chosen_exit[:-5])

        # find a room with a path-through
        #TODO: shuffle them to eliminate the extra work of getting re-testing of bad rooms?
        found = False
        random.shuffle(rooms_to_place)
        for room_name in rooms_to_place:
            room = rooms[room_name]
            # add dummy exit nodes
            room_graph, room_dummy_exits = dummy_exit_graph(room.graph, room.doors)
            room_direction = door_hookups[chosen_direction]
            # find an entrance that matches - TODO - for loop - all entrances that match
            if len(room.doors[room_direction]) == 0:
                continue
            chosen_entrance = random.choice(room.doors[room_direction])
            #TODO: where to start the BFS?
            entrance_state = BFSItemsState(chosen_entrance, exit_state.wildcards, exit_state.items, exit_state.assignments)
            paths_through, _, _ = room_graph.BFS_items(entrance_state, None, fixed_items)
            paths_through = filter_paths(paths_through, entrance_state, room_dummy_exits)
            # if there is at least one path-through - take one
            if len(paths_through) > 0:
                #print current_assignments
                #print current_wildcards
                print "Placing " + chosen_entrance + " at " + chosen_exit[:-5]
                if chosen_entrance == "Statues_L":
                    print "gotem"
                    break
                # pick a path-through to follow and update the current state.
                current_state = choose_random_state(paths_through)
                # remove "dummy"
                current_state.node = current_state.node[:-5]

                # connect the two rooms at chosen_exit , chosen_entrance
                room_unassigned_items = [x for x in room.item_nodes if x not in current_state.assignments]

                # update dummy exits!
                if chosen_entrance + "dummy" in room_dummy_exits:
                    room_graph.remove_node(chosen_entrance + "dummy")
                    room_dummy_exits.remove(chosen_entrance + "dummy")
                if chosen_exit in dummy_exits:
                    current_graph.remove_node(chosen_exit)
                    dummy_exits.remove(chosen_exit)
                chosen_exit = chosen_exit[:-5]
                dummy_exits.extend(room_dummy_exits)

                # update exits_to_connect
                # add all the exits of the new room
                # it would be nice to just add these two dicts together using a defined +
                for direction, doors in room.doors.items():
                    exits_to_connect[direction].extend(doors)
                # now get rid of the two doors we just hooked up
                exits_to_connect[chosen_direction].remove(chosen_exit)
                exits_to_connect[room_direction].remove(chosen_entrance)

                # add the graph of the other room
                current_graph.add_room(chosen_exit, chosen_entrance, room_graph)

                door_changes.append((chosen_exit, chosen_entrance))
                # now that we have placed it, get rid of it
                rooms_to_place.remove(room_name)
                found = True
                break

        # otherwise, try another room
        if not found:
            print "No rooms with a path-through"
            break
    item_changes.extend(current_state.assignments.items())
    # make the current assignment a reality (in the graph)
    # TODO: with already-assigned nodes that haven't been placed yet?
    for node, item in current_state.assignments.items():
        if node in current_graph.name_node:
            current_graph.name_node[node].data.type = item
    # place unassigned items
    #TODO: maybe do something more sophisticated to place progression items at reachable locations?
    # first, calculate the items that haven't been placed!
    for item in current_state.assignments.values():
        if item in items_to_place:
            items_to_place.remove(item)
    for item_node in unassigned_item_nodes:
        item = items_to_place.pop()
        current_graph.name_node[item_node].data.type = item
        item_changes.append(item_node, item)

    # remove dummy exits
    for exit in dummy_exits:
        current_graph.remove_node(exit)

    # now just place rooms randomly
    # while there are doors that haven't been connected
    while reduce(lambda x,y: x or y, [len(direction_doors) != 0 for direction_doors in exits_to_connect.values()]):

        # all directions that still have a door left to place
        directions_left = [direction for direction in exits_to_connect.keys() if len(exits_to_connect[direction]) != 0]

        # if there are no rooms left to place...
        if len(rooms_to_place) == 0:
            # pick a random direction with doors left to place
            direction = random.choice(directions_left)
            other_direction = door_hookups[direction]
            door = random.choice(exits_to_connect[direction])
            other_door = random.choice(exits_to_connect[other_direction])
            # update bookeeping
            exits_to_connect[direction].remove(door)
            exits_to_connect[other_direction].remove(other_door)
            door_changes.append((door, other_door))
            # add that change to the graph
            door_data = current_graph.name_node[door].data
            other_door_data = current_graph.name_node[other_door].data
            # none indicates an impassable door
            if door_data.items is not None:
                current_graph.add_edge(door, other_door, door_data.items)
            if other_door_data.items is not None:
                current_graph.add_edge(other_door, door, other_door_data.items)

        # if there are still rooms left to place
        else:
            # pick a room to place - try rooms until we can place one
            found = -1
            for index in range(len(rooms_to_place)):
                room_doors = rooms[rooms_to_place[index]].doors
                room_directions = room_doors.keys()
                random.shuffle(room_directions)
                for room_direction in room_directions:
                    # pick a representative for each direction
                    if len(room_doors[room_direction]) == 0:
                        continue
                    direction_door = random.choice(room_doors[room_direction])
                    match_direction = door_hookups[room_direction]
                    # find a match!
                    if len(exits_to_connect[match_direction]) != 0:
                        exit = random.choice(exits_to_connect[match_direction])
                        new_room = rooms[rooms_to_place[index]]
                        # link the two exits
                        # add every exit in the new room to the list of exits we must connect
                        for direction, doors in new_room.doors.items():
                            exits_to_connect[direction].extend(doors)
                        # remove the two doors we just placed
                        exits_to_connect[room_direction].remove(direction_door)
                        exits_to_connect[match_direction].remove(exit)

                        door_changes.append((direction_door, exit))

                        # update the graph
                        current_graph.add_room(exit, direction_door, new_room.graph)

                        # add items, if necessary
                        for item_node in new_room.item_nodes:
                            item = items_to_place.pop()
                            current_graph.name_node[item_node].data.type = item
                            item_changes.append((item_node, item))

                        found = index
                        break
                if found >= 0:
                    break
            # we placed the room at index - remove it
            rooms_to_place.pop(found)
        #print sum([len(dir_doors) for dir_doors in current_exits.values()])
    print "ROOMS NOT PLACED - " + str(len(rooms_to_place))
    return door_changes, item_changes, current_graph, current_state

#UNFINISHED:
def completable_rando(rooms):
    """creates the door transitions and items for a completable randomizer seed"""
    clean_rooms(rooms)
    check_door_totals(rooms)

    landing_site = rooms.pop("Landing_Site")
    current_graph = landing_site[0].graph
    exits_to_connect = landing_site[1]
    # approximate position of the ship - choose R2 so L2 will be discovered
    current_node = "Landing_Site_R2"
    # keeps track of wildcards - items we have picked up but haven't assigned
    current_wildcards = set()
    # keeps track of items we've picked up
    current_items = set()
    # keeps track of the item assignment
    current_assignment = set()
    # keeps track of exits reachable from current node
    reachable_exits = []

    # get a random order for items - used after we have assigned all of the items required to pass statues
    items_to_place = map_items()
    random.shuffle(items_to_place)

    # get a random order for rooms
    rooms_to_place = rooms.keys()
    random.shuffle(rooms_to_place)

    door_changes = []
    item_changes = []

    # make dummy exit nodes for landing_site
    dummy_exits = add_dummy_exits(current_graph, exits_to_connect)

    while True:

        reachable_exits = "sadness"
    # update reachable_exits using wildcard BFS
    # pick a reachable exit and a corresponding item assignment
    # calculate paths-through using wildcard BFS with current items for each room until we find one with a path-through
    # update items, wildcards, assignments based on that path-through
    # place that room, and go to the terminal of path_through and make dummy exit nodes

    # if rooms is empty - move on. now we just need to hook up the rest of the doors
    # if reachable exits is empty, cry
    # if there aren't any rooms with a path_through, pick a different reachable exit.

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
    rooms_to_place = rooms.keys()
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
    print "ROOMS NOT PLACED - " + str(len(rooms_to_place))
    # return the list of door and item changes
    return door_changes, item_changes, current_graph

#TODO: in alg_support?
def choose_random_state(finished):
    """chooses a random state from finished"""
    
    #TODO: quick and dirty fix
    # filter out empty entries of finished
    finished = to_states(finished)
    finished = from_states(finished)

    node = random.choice(finished.keys())
    items = random.choice(finished[node].keys())
    wildcards, assignments = random.choice(finished[node][items])
    return BFSItemsState(node, wildcards, items, assignments)

