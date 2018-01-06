
from parse_rooms import *
from rom_edit import *
from rando_algs import *

import random
import argparse
import shutil
import sys

#TODO: a better file structure would keep all the rando algorithms that produce door changes and item changes somewhere else
# this file should just be the executable
#TODO: figure out what's going on with Zip Tube
#TODO: graphical glitches after kraid? - can pause to fix, or also just leave kraid's room connected to the kraid eye door room
#TODO: sand pits don't always connect up - different sizes
#TODO: change scroll "colors" in kraid, crocomire, sporespawn, shaktool rooms?
#TODO: door leading to top of bowling turns grey once you beat phantoon?
#TODO: make the RNG seed work -> random dictionary word?
#TODO: is it possible to go back through bowling alley?
#   make the create filename with the seed
#TODO: figure out what's going on with multiple item copies
#TODO: get rid of Drain?
#TODO: make the --completable option work
#TODO: Old Mother Brain badness before zebes awake + other things with zebes waking up (last missiles)
#TODO: fix brinstar elevator stupid things?
#TODO: I got spring ball instead of morph ball?
#TODO: randomize ceres within ceres, tourian within tourian?
#TODO: Boss rush mode!
#TODO: random number of missiles / supers / pbs per expansion?

#TODO: move to rom_edit?
def rom_setup(rom, time):
    """edits rom to skip ceres, etc."""
    # skip ceres
    # TODO: this doesn't work when the rooms are randomized...?
    #write_raw_bytes(rom, "0x0016ebb", "\x05")

    # make sand easier to jump out of without gravity
    write_raw_bytes(rom, "0x2348c", "\x00")
    write_raw_bytes(rom, "0x234bd", "\x00")

    # remove gravity suit heat protection
    write_raw_bytes(rom, "0x6e37d", "\x01")
    write_raw_bytes(rom, "0x869dd", "\x01")

    # suit animation skip #TODO
    write_raw_bytes(rom, "0x20717", "\xea\xea\xea\xea")

    # fix heat damage speed echoes bug #TODO: verify
    write_raw_bytes(rom, "0x8b629", "\x01")

    # disable GT Code #TODO: verify
    write_raw_bytes(rom, "0x15491c", "\x80")

    #TODO: there's some bug here I think... :(
    # change escape timer
    # first, convert to minutes, seconds:
    minutes = time / 60
    seconds = time % 60

    # get the number as hex bytes
    minute_bytes = int_to_hex(minutes)
    second_bytes = int_to_hex(seconds)

    # can't write more than one byte!
    assert len(minute_bytes) == 1, "Minutes too long"
    assert len(second_bytes) == 1, "Seconds too long"

    # write seconds
    write_raw_bytes(rom, "0x0001e21", second_bytes)
    # write minutes
    write_raw_bytes(rom, "0x0001e22", minute_bytes)

    # apply other IPSs #TODO: make sure this works!
    apply_ips("patches/g4_skip.ips", rom)
    apply_ips("patches/max_ammo_display.ips", rom)
    apply_ips("patches/wake_zebes.ips", rom)
    #TODO: why does this break everything?
    #apply_ips("patches/introskip_doorflags.ips", rom)

#TODO: is there a possibility for a door not to be in door_changes?
def write_door_changes(door_changes, spoiler_file):
    for left, right in door_changes:
        spoiler_file.write(left + " <> " + right + "\n")

def write_item_assignments(item_assignments, spoiler_file):
    for node, item in item_assignments:
        spoiler_file.write(node + ": " + item + "\n")

def parse_starting_items(items):
    if items is None:
        return ItemSet()
    items = items.split()
    item_set = ItemSet()
    for item in items:
        item_def = item.rstrip("1234567890")
        item_set.add(item_def)
    return item_set

def remove_external_edges(graph, node):
    """Removes all edges from node to a node in another room."""
    self_room = node.split("_")[:-1]
    for edge in graph.node_edges[node]:
        edge_room = edge.terminal.split("_")[:-1]
        if edge_room != self_room:
            graph.remove_edge(node, edge.terminal)

def prepare_for_escape(graph):
    """Prepares the graph for searching for escape paths
    by removing edges that can't be used during escape."""
    remove_external_edges(graph, "Parlor_L1")
    remove_external_edges(graph, "Parlor_L2")
    remove_external_edges(graph, "Parlor_L3")
    remove_external_edges(graph, "Parlor_B")
    remove_external_edges(graph, "Parlor_R3")
    remove_external_edges(graph, "Climb_Room_R1")
    remove_external_edges(graph, "Climb_Room_R2")
    remove_external_edges(graph, "Climb_Room_R3")
    remove_external_edges(graph, "Climb_Room_L")

def seed_rng(seed):
    seed = args.seed
    if seed is None:
        seed = random.randrange(sys.maxsize)
    random.seed(seed)
    return seed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Welcome to the Super Metroid Door randomizer!")
    parser.add_argument("--clean", metavar="<filename>", required=True, help="The path to a clean rom file from the current directory.")
    parser.add_argument("--create", metavar="<filename>", required=True, help="The path to the rom file you want to create.")
    parser.add_argument("--seed", metavar="<seed>", required=False, help="The seed you want to use for the RNG.")
    parser.add_argument("--completable", action="store_true", help="generate until you find a completable map.")
    parser.add_argument("--starting_items", metavar="<item_list>", required=False, help="A list of items to start with: see Readme.md for details.")
    parser.add_argument("--graph", action="store_true", help="create a room graph spoiler file. You will need graphviz installed in your $PATH")
    #TODO argument for which algorithm to use

    args = parser.parse_args()
    seed = seed_rng(args.seed)
    spoiler_file = open(args.create + ".spoiler.txt", "w")

    # setup
    # copy it to remove Bombs
    # TODO: GET RID OF Bombs
    all_items = item_types[:]
    all_items.remove("Bombs")
    all_items = ItemSet(all_items)
    # escape timer vars
    escape_timer = 0
    tourian_time = 60
    time_per_node = 15
    starting_items = parse_starting_items(args.starting_items)

    completable = False
    while not completable:
        #TODO: re-parsing rooms is quick and dirty...
        rooms = parse_rooms("encoding/rooms.txt")
        door_changes, item_changes, graph, state = item_quota_rando(rooms, starting_items)
        # check completability - can reach statues?
        start_state = BFSState(state.node, state.items)
        end_state = BFSState("Statues_ET", ItemSet())
        path_to_statues = graph.check_completability(start_state, end_state)
        completable = path_to_statues is not None
        if completable:
            # check completability - can escape?
            items = all_items | ItemSet(["Kraid", "Phantoon", "Draygon", "Ridley"])
            prepare_for_escape(graph)
            escape_start = BFSState("Escape_4_R", items)
            escape_end = BFSState("Landing_Site_L2", items)
            escape_path = graph.check_completability(escape_start, escape_end)
            if escape_path is None: 
                completable = False
            else:
                spoiler_file.write("Path to Escape:\n")
                spoiler_file.write(str(escape_path))
                # one minute to get out of tourian, then 30 seconds per room
                #TODO: is this fair? the player might need to farm and explore...
                #TODO: simple node-length means intermediate nodes / etc. will cause problems
                escape_timer = tourian_time + time_per_node * len(escape_path)
                spoiler_file.write("\n")
                spoiler_file.write("Esape Timer: " + str(escape_timer) + " seconds\n")
        # accept the seed regardless if we don't care about completability
        if not args.completable:
            break
        # re-seed the rng for a new map (if we need to)
        if not completable and args.completable:
            seed = seed_rng(None)

    print "Completable: " + str(completable)
    print "RNG SEED - " + str(seed)

    spoiler_file.write("ITEMS:\n")
    write_item_assignments(item_changes, spoiler_file)

    spoiler_file.write("DOORS:\n")
    write_door_changes(door_changes, spoiler_file)

    # make the spoiler graph
    if args.graph:
        import spoiler_graph 
        spoiler_graph.make_spoiler_graph(door_changes, args.create)

    # now that we have the door changes and the item changes, implement them!
    # first, make the new rom file:
    shutil.copyfile(args.clean, args.create)
    rom_setup(args.create, escape_timer)
    if args.starting_items is not None:
        make_starting_items(args.starting_items, args.create)

    # then make the necessary changes
    make_items(item_changes, args.create)
    make_doors(door_changes, args.clean, args.create)


#TODO: these are some things I noted earlier about the escape paths
# find the escape path
# TODO: am I really going to assume they picked up everything? this might make escape pretty hard...
# TODO: find a way to disable grey doors during escape
# TODO: might wanna make sure they don't have to, like, defeat crocomire during escape
# or at least they have the time necessary to do so :P
# - to do this: if there's a "problematic" node in the shortest escape path,
# remove it from the graph and do another BFS. If there's no path, then award them time to beat that node
# If there is another path, then just award them time to complete that path

