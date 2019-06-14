from encoding.parse_rooms import *
from rom_tools.rom_edit import *
from door_rando.rando_algs import *
from encoding import sm_global
from rom_tools.rom_manager import *

import door_rando.settings
from misc import rng
from misc import settings_parse

import random
import argparse
import shutil
import sys

#TODO: A better file structure would keep all the rando algorithms that produce door changes and item changes somewhere else
# this file should just be the executable
#TODO: Fix Zip Tube by removing the door ASM from the doors that lead into it in vanilla, and adding the same ASM to the doors that lead into it on the randomized ROM
#TODO: Fix graphical glitches after Kraid by setting the "Reload CRE" flag in the room headers of the rooms adjacent to Kraid's room.
#TODO: Sand pits don't always connect up - different sizes
#TODO: Add grey door caps to the back side of boss rooms. Do this by finding the appropriate door in the actual level data to determine the position and facing of the door cap, then adding a new PLM to the room (reallocating the PLMs as necessary)
#TODO: Door leading to top of bowling should not turn grey after you beat Phantoon.
#TODO: Is it possible to go back through bowling alley?
#TODO: Make the create filename with the seed
#TODO: Get rid of Drain?
#TODO: Old Mother Brain badness before zebes awake + other things with zebes waking up (last missiles)
#TODO: Fix brinstar elevator stupid things?
#TODO: Randomize ceres within ceres, tourian within tourian?
#   - general "keep the same area" randomization?
#TODO: Boss rush mode!
#TODO: Random number of missiles / supers / pbs per expansion?
#TODO: timeout for the completability check...

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

def get_args():
    parser = argparse.ArgumentParser(description="Welcome to the Super Metroid Door randomizer!")
    parser.add_argument("--clean", metavar="<filename>", required=True, help="The path to a clean rom file from the current directory.")
    parser.add_argument("--create", metavar="<filename>", required=True, help="The path to the rom file you want to create.")
    parser.add_argument("--seed", metavar="<seed>", required=False, help="The seed you want to use for the RNG.")
    parser.add_argument("--completable", action="store_true", help="generate until you find a completable map.")
    parser.add_argument("--starting_items", metavar="<item_list>", required=False, help="A list of items to start with: see Readme.md for details.")
    parser.add_argument("--graph", action="store_true", help="create a room graph spoiler file. You will need graphviz installed in your $PATH")
    parser.add_argument("--debug", action="store_true", required=False, help="print debug information while creating the room layout.")
    parser.add_argument("--settings", metavar="<folder>", required=False, help="The path to a folder with settings files. Used for updating things like what items the randomizer will use")
    #TODO argument for which algorithm to use
    args = parser.parse_args()
    return args

def main():
    args = get_args()
    seed = rng.seed_rng(args.seed)
    print(args.settings)
    spoiler_file = open(args.create + ".spoiler.txt", "w")

    # Setup
    # Copy it to remove Bombs
    # TODO: GET RID OF Bombs
    all_items = sm_global.items[:]
    all_items = ItemSet(all_items)
    # escape timer vars
    escape_timer = 0
    tourian_time = 60
    time_per_node = 15
    starting_items = parse_starting_items(args.starting_items)

    completable = False
    while not completable:
        #TODO: re-parsing rooms is quick and dirty...
        rooms = parse_rooms("encoding/dsl/rooms.txt")
        door_changes, item_changes, graph, state = item_quota_rando(rooms, args.debug, starting_items)
        # Check completability - can reach statues?
        start_state = BFSState(state.node, state.items)
        end_state = BFSState("Statues_ET", ItemSet())
        path_to_statues = graph.check_completability(start_state, end_state)
        completable = path_to_statues is not None
        if completable:
            # Check completability - can escape?
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
                #TODO: Is this fair? the player might need to farm and explore...
                #TODO: Simple node-length means intermediate nodes / etc. will cause problems
                # give the player time to defeat minibosses, or go through long cutscenes
                for node in escape_path:
                    if node == "Crocomire_T":
                        escape_timer += (70 - 2*time_per_node)
                    elif node == "Spore_Spawn_B":
                        escape_timer += (45 - 2*time_per_node)
                    elif node == "Golden_Torizo_R":
                        escape_timer += (45 - 2*time_per_node)
                    elif node == "Shaktool_L":
                        escape_timer += (50 - 2*time_per_node)
                    elif node == "Bowling_Alley_L2":
                        escape_timer += (50 - 2*time_per_node)
                escape_timer = tourian_time + time_per_node * len(escape_path)
                spoiler_file.write("\n")
                spoiler_file.write("Esape Timer: " + str(escape_timer) + " seconds\n")
        # Accept the seed regardless if we don't care about completability
        if not args.completable:
            break
        # Re-seed the rng for a new map (if we need to)
        if not completable and args.completable:
            print("Not Completable")
            seed = rng.seed_rng(None)

    print("Completable: " + str(completable))
    print("RNG SEED - " + str(seed))

    spoiler_file.write("ITEMS:\n")
    write_item_assignments(item_changes, spoiler_file)

    spoiler_file.write("DOORS:\n")
    write_door_changes(door_changes, spoiler_file)

    # Make the spoiler graph
    if args.graph:
        from door_rando import spoiler_graph 
        spoiler_graph.make_spoiler_graph(door_changes, args.create)

    # Now that we have the door changes and the item changes, implement them!
    # First, make the new rom file:
    rom = RomManager(args.clean, args.create)
    rom.set_escape_timer(escape_timer)
    if args.starting_items is not None:
        make_starting_items(args.starting_items, rom)

    # Then make the necessary changes
    make_items(item_changes, rom)
    make_doors(door_changes, rom)
    make_saves(door_changes, rom)

    # Save out the rom
    rom.save_and_close()

if __name__ == "__main__":
    main()

#TODO: these are some things I noted earlier about the escape paths
# find the escape path
# TODO: am I really going to assume they picked up everything? this might make escape pretty hard...
# TODO: find a way to disable grey doors during escape
# TODO: might wanna make sure they don't have to, like, defeat crocomire during escape
# or at least they have the time necessary to do so :P
# Instead: if there's a "problematic" node in the shortest escape path,
# remove it from the graph and do another BFS. If there's no path, then award them time to beat that node
# If there is another path, then just award them time to complete that path

