
from alg_support import *
import random

#TODO: some of the outputs for this don't make sense - for example it placed Space Jump then gave up (instead of putting a Super at space jump.)
#TODO: This currently places a room at Warehouse_Zeelas_L2 without having Kraid
# -> something is broken :(
#TODO: This doesn't always take the "right" path-through. For example,
# with Hopper_Energy, there are two paths from L. L, and L -> E -> L.
# if L -> E -> L isn't taken, we don't wind up with the item like usual.
# also with Alpha_Power_Bombs

# new idea - give the player some items, then just randomly place the rest of the map
def item_quota_rando(rooms, nitems=6):
    clean_rooms(rooms)
    check_door_totals(rooms)

    landing_site = rooms.pop("Landing_Site")
    current_graph = landing_site[0].graph
    exits_to_connect = landing_site[1]

    # keeps track of the current BFS state
    current_state = BFSItemsState("Landing_Site_R2")

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

    # make dummy exit nodes for landing_site - these dummy exits serve to let the BFS search not just reachable doors, but enterable doors.
    current_graph, dummy_exits = dummy_exit_graph(current_graph, exits_to_connect)

    #TODO: maybe doing this places too many items too early?
    while len(rooms_to_place) > 0:
    #while len(current_items) < nitems:
        # wildcard BFS to find reachable exits
        #print "loop"
        #print current_state.node
        #print current_state.wildcards
        bfs_finished, _, _ = current_graph.BFS_items(current_state, None, fixed_items)
        # dict comprehensions! - filter bfs_finished for the entries that are dummy exits, and actually have a path to them.
        reachable_exits = {exit: bfs_finished[exit] for exit in dummy_exits if len(bfs_finished[exit]) != 0}

        #TODO: I think this works now... Consider multiple backtracks?
        # if there are more reachable exits by backtracking, do so!
        # choose a random (already-placed) door that this door can hook up with
        current_node = current_state.node
        current_direction = door_direction(current_node)
        # if we haven't already connected the current exit and if there is a valid backtracking exit
        if current_node in exits_to_connect[current_direction] and len(exits_to_connect[door_hookups[current_direction]]) > 0:
            backtrack_exit = random.choice(exits_to_connect[door_hookups[current_direction]])
                        #print "backtracking to: " + backtrack_exit
            # pretend like they are connected - remove their dummy nodes from the list of dummies...
            # make a shallow copy first - if it turns out that backtracking was a bad decision, we need the original
            dummy_copy = dummy_exits[:]
            if current_node + "dummy" in dummy_copy:
                dummy_copy.remove(current_node + "dummy")
            if backtrack_exit + "dummy" in dummy_copy:
                dummy_copy.remove(backtrack_exit + "dummy")
            # and put edges between them
            current_exit_constraints = current_graph.name_node[current_node].data.items
            backtrack_exit_constraints = current_graph.name_node[backtrack_exit].data.items
            if current_exit_constraints is not None:
                current_graph.add_edge(current_node, backtrack_exit, current_exit_constraints)
            if backtrack_exit_constraints is not None:
                current_graph.add_edge(backtrack_exit, current_node, backtrack_exit_constraints)

            # find the reachable exits under the new scheme (start from current node, to ensure you can get to backtrack exit)
            backtrack_finished, _, _ = current_graph.BFS_items(current_state, None, fixed_items)
            backtrack_exits = {exit: backtrack_finished[exit] for exit in dummy_copy if len(bfs_finished[exit]) != 0}
            #print len(backtrack_exits)
            #print len(reachable_exits)

            #TODO: greater than or equal to?
            # if there are more reachable exits by backtracking, do so!
            if len(backtrack_exits.keys()) > len(reachable_exits.keys()):
                print "BACKTRACKED!"
                # those dummy exits aren't there anymore
                # remove the actual dummy exits from the graph
                if current_node + "dummy" in dummy_exits:
                    current_graph.remove_node(current_node + "dummy")
                if backtrack_exit + "dummy" in dummy_exits:
                    current_graph.remove_node(backtrack_exit + "dummy")
                # the copied dummy already has those exits removed.
                dummy_exits = dummy_copy
                # we no longer have to connect them
                exits_to_connect[current_direction].remove(current_node)
                exits_to_connect[door_hookups[current_direction]].remove(backtrack_exit)
                # update door changes
                door_changes.append((current_node, backtrack_exit))
                # set reachable exits so that the next part works
                reachable_exits = backtrack_exits
            # otherwise, repair the damage to the graph and keep going
            else:
                if current_exit_constraints is not None:
                    current_graph.remove_edge(current_node, backtrack_exit)
                if backtrack_exit_constraints is not None:
                    current_graph.remove_edge(backtrack_exit, current_node)


        if len(reachable_exits.keys()) == 0:
            # if there aren't any reachable exits, place the rest of the rooms at random - hopefully there's a path to statues :)
            break
            #assert False, "No reachable exits: \n" + str(door_changes) + "\n" + str(current_assignments)
        
        chosen_exit = random.choice(reachable_exits.keys())
        chosen_path = random.choice(reachable_exits[chosen_exit])
        # update with the choices we made to use that path
        current_state.wildcards, current_state.items, current_state.assignments = chosen_path
        chosen_direction = door_direction(chosen_exit[:-5])

        # find a room with a path-through
        found = False
        for room_name in rooms_to_place:
            room = rooms[room_name]
            # add dummy exit nodes
            room_graph, room_dummy_exits = dummy_exit_graph(room[0].graph, room[1])
            room_direction = door_hookups[chosen_direction]
            # find an entrance that matches - TODO - for loop - all entrances that match
            if len(room[1][room_direction]) == 0:
                continue
            chosen_entrance = random.choice(room[1][room_direction])
            entrance_state = BFSItemsState(chosen_entrance, current_state.wildcards, current_state.items, current_state.assignments)
            paths_through, _, _ = room_graph.BFS_items(entrance_state, None, fixed_items)
            #TODO: have filter_paths take a state
            filter_paths(paths_through, chosen_entrance, current_state.wildcards, current_state.items, room_dummy_exits)
            #print paths_through
            # if there is at least one path-through - take one
            if len(paths_through) > 0:
                #print current_assignments
                #print current_wildcards
                print "Placing " + chosen_entrance + " at " + chosen_exit[:-5]
                # if we follow a path-through, update current_node, etc.
                chosen_room_path = random.choice(paths_through.keys())
                # remove "dummy"
                current_state.node = chosen_room_path[:-5]
                #print paths_through
                #print paths_through[chosen_room_path]
                current_state.wildcards, current_state.items, current_state.assignments = paths_through[chosen_room_path][0] #is 0 the right one?

                # connect the two rooms at chosen_exit , chosen_entrance
                room_unassigned_items = [x for x in room[2] if x not in current_state.assignments]

                # update dummy exits!
                if chosen_entrance + "dummy" in room_dummy_exits:
                    room_graph.remove_node(chosen_entrance + "dummy")
                    room_dummy_exits.remove(chosen_entrance + "dummy")
                if chosen_exit in dummy_exits:
                    current_graph.remove_node(chosen_exit)
                    dummy_exits.remove(chosen_exit)
                chosen_exit = chosen_exit[:-5]
                dummy_exits.extend(room_dummy_exits)

                #update exits_to_connect
                # add all the exits of the new room
                for direction, doors in room[1].items():
                    exits_to_connect[direction].extend(doors)
                # now get rid of the two doors we just hooked up
                exits_to_connect[chosen_direction].remove(chosen_exit)
                exits_to_connect[room_direction].remove(chosen_entrance)
                current_graph.add_room(chosen_exit, chosen_entrance, room_graph)

                door_changes.append((chosen_exit, chosen_entrance))
                # now that we have placed it, get rid of it
                rooms_to_place.remove(room_name)
                found = True
                break

            # otherwise, try another room
    if not found:
        assert False, "No rooms with a path-through"
        print "Loop end"
    item_changes.extend(current_state.assignments.items())
    # make the current assignment a reality (in the graph)
    for node, item in current_state.assignments.items():
        current_graph.name_node[node].data.type = item
    #print door_changes
    #print current_items
    #print current_wildcards
    #print unassigned_item_nodes
    # place unassigned items
    #TODO: maybe do something more sophisticated to place progression items at reachable locations?
    # first, calculate the items that haven't been placed!
    for item in current_state.assignments.values():
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
                    if len(exits_to_connect[match_direction]) != 0:
                        exit = random.choice(exits_to_connect[match_direction])
                        new_room = rooms[rooms_to_place[index]]
                        # link the two exits
                        # add every exit in the new room to the list of exits we must connect
                        for direction, doors in new_room[1].items():
                            exits_to_connect[direction].extend(doors)
                        # remove the two doors we just placed
                        exits_to_connect[room_direction].remove(direction_door)
                        exits_to_connect[match_direction].remove(exit)

                        door_changes.append((direction_door, exit))

                        # update the graph
                        current_graph.add_room(exit, direction_door, new_room[0].graph)

                        # add items, if necessary
                        for item_node in new_room[2]:
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

    return door_changes, item_changes, current_graph

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



