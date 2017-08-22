
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
#TODO: make sand easier to jump out of - write 00 to 0x2348c and 00 to 0x234bd ?
	# Botwoon_Energy_Farm doesn't require any items now
	# Both sand halls can be done with HJ
	# Butterfly room doesn't require HJ
	# colosseum can be done with either only gravity or only grapple beam :D
#TODO: change scroll "colors" in kraid, crocomire, sporespawn, shaktool rooms?
#TODO: G4 and varia cutscene .ipss
#TODO: door leading to top of bowling turns grey once you beat phantoon?

def rom_setup(rom, time):
	"""edits rom to skip ceres, etc."""
	# skip ceres
	# TODO: this doesn't really work when the rooms are randomized...?
	#write_raw_bytes(rom, "0x0016ebb", "\x05")


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

	#TODO: apply other IPSs

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
	#TODO argument for algorithm to use

	args = parser.parse_args()

	seed = seed_rng(args.seed)

	spoiler_file = open(args.create + ".spoiler.txt", "w")

	# setup
	rooms = parse_rooms("encoding/rooms.txt")
	all_items = set(item_types)
	all_items.remove("Bombs")
	all_items.add("B")
	escape_timer = 0

	if args.completable:
		completable = False
		while not completable:
			door_changes, item_changes, graph = basic_rando(rooms)
			# check completability - make item assignment
			#items_finished, _, _ = graph.BFS_items("Landing_Site_L2", "Statues_ET")
			#print items_finished["Statues_ET"]

			# check completability - get to golden statues with all items
			bfs_offers, bfs_finished, bfs_found, bfs_set = graph.BFS_target("Landing_Site_L2", ("Statues_ET", all_items), all_items)
			completable = bfs_found
			#if len(items_finished["Statues_ET"]) == 0: completable = False
			seed = seed_rng(None)
			rooms = parse_rooms("encoding/rooms.txt")
			
			if completable:
				# find the path to statues
				node = "Statues_ET"
				items = bfs_set
				path_to_statues = []
				# trace back
				while node != "Landing_Site_L2" or items != all_items:
					path_to_statues.insert(0, node)
					next_p = [next_n[1] for next_n in bfs_offers[node] if next_n[0] == items]
					node, items = next_p[0]
				spoiler_file.write("Path to Statues:\n")
				spoiler_file.write(str(path_to_statues))
				spoiler_file.write("\n")

				# find the escape path
				escape_path = []
				# TODO: am I really going to assume they picked up everything? this might make escape pretty hard...
				# TODO: find a way to disable grey doors during escape
				# TODO: might wanna make sure they don't have to, like, defeat crocomire during escape
				# or at least they have the time necessary to do so :P
				# - to do this: if there's a "problematic" node in the shortest escape path,
				# remove it from the graph and do another BFS. If there's no path, then award them time to beat that node
				# If there is another path, then just award them time to complete that path
				items = all_items | set(["Kraid", "Phantoon", "Draygon", "Ridley"])
				bfs_offers, bfs_finished, bfs_found, bfs_set = graph.BFS_target("Escape_4_R", ("Landing_Site_L2", items), items)
				node = "Landing_Site_L2"

				# trace back
				assert bfs_found, "CANT ESCAPE!"
				#TODO: BFS_traceback function
				while node != "Escape_4_R":
					escape_path.insert(0, node)
					next_p = [next_n[1] for next_n in bfs_offers[node] if next_n[0] == items]
					node, items = next_p[0]
				spoiler_file.write("Path to Escape:\n")
				spoiler_file.write(str(escape_path))
				# one minute to get out of tourian, then 20 seconds per room
				#TODO: is this fair? the player might need to farm and explore...
				escape_time = 60 + 10 * len(escape_path)
				spoiler_file.write("\n")
				spoiler_file.write("Esape Timer: " + str(escape_time))
	else:
		#door_changes, item_changes, graph = basic_rando(rooms)
		door_changes = []
		item_changes = []
		door_changes, item_changes, graph = item_quota_rando(rooms)

		# check completability - get to golden statues with all items
		bfs_offers, bfs_finished, bfs_found, bfs_set = graph.BFS_target("Landing_Site_L2", ("Statues_ET", set()))
		print bfs_finished["Statues_L"]
		print bfs_finished["Statues_ET"]
		print "Completable: " + str(bfs_found)
		bfs_offers, bfs_finished, bfs_found, bfs_set = graph.BFS_target("Landing_Site_L2", ("Statues_ET", all_items), all_items)
		print bfs_finished["Statues_ET"]
		print "Completable: " + str(bfs_found)
		if bfs_found:
			node = "Statues_ET"
			items = bfs_set
			path_to_statues = []
			while node != "Landing_Site_L2" or items != all_items:
				path_to_statues.insert(0, node)
				next_p = [next_n[1] for next_n in bfs_offers[node] if next_n[0] == items]
				node, items = next_p[0]
			print path_to_statues
			

	print "RNG SEED - " + str(seed)

	# now that we have the door changes and the item changes, implement them!
	# first, make the new rom file:
	shutil.copyfile(args.clean, args.create)
	rom_setup(args.create, escape_timer)

	# then make the necessary changes
	make_items(item_changes, args.create)
	make_doors(door_changes, args.clean, args.create)