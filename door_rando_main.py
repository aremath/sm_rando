# Python Imports
import argparse
import sys
from collections import defaultdict, deque

# Internal imports
from encoding import parse_rooms, sm_global
from rom_tools.rom_edit import make_items, make_saves, make_doors, fix_skyscroll, logic_improvements, make_starting_items
from rom_tools.rom_manager import RomManager
from door_rando import settings
from door_rando.rando_algs import item_quota_rando
from door_rando.alg_support import get_fixed_items
from data_types.item_set import ItemSet
from data_types.constraintgraph import BFSState
from misc import rng, settings_parse

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
#TODO: Fix brinstar elevator stupid things?
#TODO: Randomize ceres within ceres, tourian within tourian?
#   - general "keep the same area" randomization?
#TODO: Boss rush mode!
#TODO: Random number of missiles / supers / pbs per expansion?
#TODO: timeout for the completability check...
#TODO: extraneous _int_ nodes make it into the escape path

#TODO: is there a possibility for a door not to be in door_changes?
def write_door_changes(door_changes, spoiler_file):
    for left, right in door_changes:
        spoiler_file.write(left + " <> " + right + "\n")

def write_item_assignments(item_assignments, spoiler_file):
    for node, item in item_assignments:
        spoiler_file.write(node + ": " + item + "\n")

def parse_starting_items(items):
    """Parses the CLI starting items into an ItemSet"""
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

# Node Name -> Node Item
boss_items = {
    "Kraid_Kraid": "Kraid",
    "Phantoon_Phantoon": "Phantoon",
    "Draygon_Draygon": "Draygon",
    "Ridley_Ridley": "Ridley",
    "Botwoon_Botwoon": "Botwoon",
    "Spore_Spawn_Spore_Spawn": "Spore_Spawn",
    "Golden_Torizo_Golden_Torizo": "Golden_Torizo",
    "Bomb_Torizo_Bomb_Torizo": "Bomb_Torizo",
    "Mother_Brain_Mother_Brain": "Mother_Brain",
    "Crocomire_Crocomire": "Crocomire",
}

# Item nodes is Node Name -> Node Item
#TODO: remove "_int_" nodes that were created when computing backtracks
def remove_loops(path, starting_items, item_nodes):
    """
    Simplify a path with cycles to create a minimal spoiler path
    """
    # Add bosses to item_nodes
    item_nodes.update(boss_items)
    # Node name -> node neighbors
    nodes = defaultdict(list)
    item_set = starting_items
    # Build a mini-graph of states
    for i, node in enumerate(path[:-1]):
        if node in item_nodes:
            item_set |= ItemSet([item_nodes[node]])
        state = (node, item_set)
        next_node = path[i+1]
        if next_node in item_nodes:
            next_item_set = item_set | ItemSet([item_nodes[next_node]])
        else:
            next_item_set = item_set
        next_state = (next_node, next_item_set)
        nodes[state].append(next_state)
    print(item_set)
    print([n for n in nodes if n[0] == path[-1]])
    # Now BFS
    start = (path[0], starting_items)
    end = (path[-1], item_set)
    offers = {start: start}
    # Use a dict to avoid set hashing RNG (now that dicts order is determinisitic)
    finished = {start: None}
    queue = deque([start])
    while len(queue) > 0:
        node = queue.popleft()
        if node == end:
            break
        for neighbor in nodes[node]:
            if neighbor not in finished:
                queue.append(neighbor)
                finished[neighbor] = None
                offers[neighbor] = node
    # Now decode offers to get the path
    assert end in finished
    out_path = []
    current_node = end
    while current_node != start:
        out_path.append(current_node)
        current_node = offers[current_node]
    out_path.append(current_node)
    return out_path[::-1]

def pretty_print_out_path(f, out_path):
    current_item_set = out_path[0][1]
    for node, item_set in out_path:
        f.write(node)
        f.write(" -> ")
        if item_set != current_item_set:
            f.write("\n")
            f.write("Pick up item: {}\n".format(item_set - current_item_set))
            current_item_set = item_set
    return

def get_args(arg_list):
    #print(arg_list)
    parser = argparse.ArgumentParser(description="Welcome to the Super Metroid Door randomizer!")
    parser.add_argument("--clean", metavar="<filename>", required=True, help="The path to a clean rom file from the current directory.")
    parser.add_argument("--create", metavar="<filename>", required=True, help="The path to the rom file you want to create.")
    parser.add_argument("--seed", metavar="<seed>", required=False, help="The seed you want to use for the RNG.")
    parser.add_argument("--completable", action="store_true", help="generate until you find a completable map.")
    parser.add_argument("--starting_items", metavar="<item_list>", required=False, help="A list of items to start with: see Readme.md for details.")
    parser.add_argument("--graph", action="store_true", help="create a room graph spoiler file. You will need graphviz installed in your $PATH")
    parser.add_argument("--debug", action="store_true", required=False, help="print debug information while creating the room layout.")
    parser.add_argument("--settings", metavar="<folder>", required=False, help="The path to a folder with settings files. Used for updating things like what items the randomizer will use")
    parser.add_argument("--g8", action="store_true", required=False, help="If set, will change the Crateria map room into a second copy of the G4 room.")
    parser.add_argument("--doubleboss", action="store_true", required=False, help="If set, adds a second copy of each boss room. Each boss still only needs to be defeated once.")
    parser.add_argument("--hard_mode", action="store_true", required=False, help="Enables hard mode logic for all rooms.")
    parser.add_argument("--noescape", action="store_true", required=False, help="If set, cannot soft-reset during the escape sequence.")
    parser.add_argument("--logfile", metavar="<filename>", required=False, help="The path to a log file to use for standard out")
    #TODO argument for which algorithm to use
    args = parser.parse_args(arg_list)
    return args

def main(arg_list):
    args = get_args(arg_list)
    # Hijack stdout for output
    if args.logfile is not None:
        sys.stdout = open(args.logfile, "w")
    seed = rng.seed_rng(args.seed)
    spoiler_file = open(args.create + ".spoiler.txt", "w")
    # Update the settings from JSON files
    if args.settings is not None:
        settings_parse.get_settings(settings.setting_paths, args.settings)

    # Setup
    # Copy it to remove Bombs
    # TODO: GET RID OF Bombs
    all_items = sm_global.items[:]
    all_items = ItemSet(all_items)

    escape_timer = 0

    starting_items = parse_starting_items(args.starting_items)
    items_to_place = settings.items_to_item_list(settings.items)

    completable = False
    while not completable:
        #TODO: re-parsing rooms is quick and dirty...
        if args.hard_mode:
            rooms = parse_rooms.parse_rooms("encoding/dsl/rooms_hard.txt")
        else:
            rooms = parse_rooms.parse_rooms("encoding/dsl/rooms.txt")
        # Phantoon means an extra L door - mercilessly destroy the maridia map station
        if args.doubleboss:
            del rooms["Maridia_Map"]
        # Remove the double boss rooms
        else:
            second_boss_rooms = ["Kraid2", "Phantoon2", "Draygon2", "Ridley2"]
            for boss_room in second_boss_rooms:
                if boss_room in rooms:
                    del rooms[boss_room]
        door_changes, item_changes, graph, state, path = item_quota_rando(rooms, args.debug, starting_items, items_to_place[:])
        # Check completability - can reach statues?
        start_state = BFSState(state.node, state.items)
        # This takes too long
        #start_state = BFSState("Landing_Site_R2", ItemSet())
        end_state = BFSState("Statues_ET", ItemSet())
        path_to_statues = graph.check_completability(start_state, end_state)
        final_path = path_to_statues
        escape_path = None
        completable = path_to_statues is not None
        if completable:
            final_path = path + path_to_statues
            final_path = remove_loops(final_path, starting_items, {k:v for k,v in item_changes})
            print(final_path[-1])
            # Check completability - can escape?
            items = all_items | ItemSet(["Kraid", "Phantoon", "Draygon", "Ridley"])
            prepare_for_escape(graph)
            escape_start = BFSState("Escape_4_R", items)
            escape_end = BFSState("Landing_Site_L2", items)
            escape_path = graph.check_completability(escape_start, escape_end)
            if escape_path is None:
                completable = False
            else:
                # One minute to get out of tourian, then 30 seconds per room
                #TODO: Is this fair? the player might need to farm and explore...
                #TODO: Simple node-length means intermediate nodes / etc. will cause problems
                # give the player time to defeat minibosses, or go through long cutscenes
                for node in escape_path:
                    if node in settings.escape:
                        escape_timer += (settings.escape[node] - 2*settings.escape["per_node"])
                escape_timer += settings.escape["tourian"] + settings.escape["per_node"] * len(escape_path)
        # Accept the seed regardless if we don't care about completability
        if not args.completable:
            break
        # Re-seed the rng for a new map (if we need to)
        if not completable and args.completable:
            print("Not Completable")
            seed = rng.seed_rng(None)

    print("Completable: " + str(completable))
    print("RNG SEED - " + str(seed))

    # Write the seed
    spoiler_file.write("RNG Seed: {}\n".format(str(seed)))
    spoiler_file.write("Items Placed: {}\n".format(str(items_to_place)))

    # Write the escape path
    if escape_path is not None:
        spoiler_file.write("Path to Escape:\n")
        spoiler_file.write(str(escape_path))
        spoiler_file.write("\n")
        spoiler_file.write("Esape Timer: {} seconds\n".format(escape_timer))

    # Write the path to the statues (including every boss)
    spoiler_file.write("Path to Statues:\n")
    if final_path is not None:
        pretty_print_out_path(spoiler_file, final_path)
    #spoiler_file.write(str(final_path))
    spoiler_file.write("\n")

    # Write the items, doors etc.
    spoiler_file.write("ITEMS:\n")
    write_item_assignments(item_changes, spoiler_file)

    spoiler_file.write("DOORS:\n")
    write_door_changes(door_changes, spoiler_file)
    spoiler_file.close()

    # Make the spoiler graph
    if args.graph:
        from door_rando import spoiler_graph
        spoiler_graph.make_spoiler_graph(door_changes, args.create)

    # Now that we have the door changes and the item changes, implement them!
    # First, make the new rom file:
    rom = RomManager(args.clean, args.create)

    # Make the rest of the necessary changes
    rom.set_escape_timer(escape_timer)
    if args.starting_items is not None:
        make_starting_items(args.starting_items, rom)

    # Apply teleportation patch
    if args.noescape:
        rom.apply_ips("patches/teleport_refill.ips")
    else:
        rom.apply_ips("patches/teleport.ips")

    # Then make the necessary changes
    make_items(item_changes, rom)
    extra_from, extra_to = logic_improvements(rom, args.g8, args.doubleboss)
    make_doors(door_changes, rom, extra_from, extra_to)
    make_saves(door_changes, rom, extra_from)
    fix_skyscroll(door_changes, rom, extra_from)

    # Logic improvements must happen last since they may
    # copy PLMs, which can be edited via prior changes

    # Save out the rom
    rom.save_and_close()

    # Collect output info
    out = {}
    out["seed"] = str(seed)
    return out

if __name__ == "__main__":
    main(sys.argv[1:])

#TODO: these are some things I noted earlier about the escape paths
# find the escape path
# TODO: am I really going to assume they picked up everything? this might make escape pretty hard...
# TODO: find a way to disable grey doors during escape
# TODO: might wanna make sure they don't have to, like, defeat crocomire during escape
# or at least they have the time necessary to do so :P
# Instead: if there's a "problematic" node in the shortest escape path,
# remove it from the graph and do another BFS. If there's no path, then award them time to beat that node
# If there is another path, then just award them time to complete that path
