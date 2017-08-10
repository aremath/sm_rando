from parse_rooms import *
from rom_edit import *

import random
import argparse
import shutil
import sys

#TODO: a better file structure would keep all the rando algorithms that produce door changes and item changes somewhere else
# this file should just be the executable
#TODO: figure out what's going on with Zip Tube
#TODO: graphical glitches after kraid? why?
#TODO: sand pits don't always connect up - different sizes

def basic_rando(rooms):
	landing_site = rooms.pop("Landing_Site")
	current_graph = landing_site[0].graph
	current_exits = landing_site[1]

	#TODO: this doesn't quite work... poping a room means I don't want to randomize any of its doors

	# get rid of pants_right - we're not using it.
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

	#TODO: this doesn't quite work either - the resulting graph is messed up!
	# doesn't matter for the Pants room, but doesn't allow travel through escape, for example...

	# don't randomize Statues_ET
	rooms["Statues"][1]["ET"].remove("Statues_ET")
	# don't randomize Escape_4_L
	rooms["Escape_4"][1]["L"].remove("Escape_4_L")
	# don't randomize Pants_R2 or Pants_L2
	rooms["Pants"][1]["R"].remove("Pants_R2")
	rooms["Pants"][1]["L"].remove("Pants_L2")

	door_totals = collections.Counter()
	# check the total number of doors:
	for room in rooms.values():
		room_doors = room[1]
		for direction, dir_doors in room_doors.items():
			door_totals[direction] += len(dir_doors)
	for door, partner in door_hookups.items():
		assert door_totals[door] == door_totals[partner], door + ": " + str(door_totals[door]) + ", " + partner + ": " + str(door_totals[partner])

	# get a random order for items
	items_to_place = item_types + 45 * ["M"] + 9 * ["S"] + 9 * ["S"] + 13 * ["E"] + 2 * ["RT"]
	# stupid special cases
	items_to_place.remove("Bombs")
	items_to_place.append("B")
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
	
	# add the new room to the graph:
	for node_name, node in new_room[0].graph.name_node.items():
		graph.add_node(node_name, node.data)
	for node_name, node_edges in new_room[0].graph.node_edges.items():
		for edge in node_edges:
			graph.add_edge(node_name, edge.terminal, edge.items)

	# connect up the two doors!
	door1_data = graph.name_node[door1].data
	door2_data = graph.name_node[door2].data
	# none means an impassable door
	if door1_data.items is not None:
		graph.add_edge(door1, door2, door1_data.items)
	if door2_data.items is not None:
		graph.add_edge(door2, door1, door2_data.items)

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


def seed_rng(seed):
	seed = args.seed
	if seed is None:
		seed = random.randrange(sys.maxsize)
	random.seed(seed)
	return seed

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

	# get the number as hex
	minute_hex = "%x" % minutes
	# pad with zeroes so even length
	minute_hex = ("0" * (len(minute_hex) % 2)) + minute_hex
	# decode it as hex bytes
	minute_bytes = (minute_hex).decode("hex")
	# do the same for seconds
	second_hex = "%x" % seconds
	second_hex = ("0" * (len(second_hex) % 2)) + second_hex
	second_bytes = (second_hex).decode("hex")

	assert len(minute_bytes) == 1, "Minutes too long"
	assert len(second_bytes) == 1, "Seconds too long"

	# write seconds
	write_raw_bytes(rom, "0x0001e21", second_bytes)
	# write minutes
	write_raw_bytes(rom, "0x0001e22", minute_bytes)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Welcome to the Super Metroid Door randomizer!")
	parser.add_argument("--clean", metavar="<filename>", required=True, help="The path to a clean rom file from the current directory.")
	parser.add_argument("--create", metavar="<filename>", required=True, help="The path to the rom file you want to create.")
	parser.add_argument("--seed", metavar="<seed>", required=False, help="The seed you want to use for the RNG.")
	parser.add_argument("--completable", action="store_true", help="generate until you find a completable map.")
	#TODO argument for algorithm to use

	args = parser.parse_args()

	seed = seed_rng(args.seed)

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
			# check completability - get to golden statues with all items
			bfs_offers, bfs_finished, bfs_found, bfs_set = graph.BFS_target("Landing_Site_L2", ("Statues_ET", all_items), all_items)
			completable = bfs_found
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
				print path_to_statues

				# find the escape path
				escape_path = []
				# TODO: am I really going to assume they picked up everything? this might make escape pretty hard...
				# TODO: find a way to disable grey doors during escape
				# TODO: might wanna make sure they don't have to, like, defeat crocomire during escape
				# or at least they have the time necessary to do so :P
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
				print escape_path
				# one minute to get out of tourian, then 20 seconds per room
				#TODO: is this fair? the player might need to farm and explore...
				escape_time = 60 + 10 * len(escape_path)
				print "Esape Timer:" + escape_time
	else:
		door_changes, item_changes, graph = basic_rando(rooms)

		# check completability - get to golden statues with all items
		bfs_offers, bfs_finished, bfs_found = graph.BFS_target("Landing_Site_L2", ("Statues_ET", all_items))
		print "Completable: " + str(bfs_found)

	print "RNG SEED - " + str(seed)

	# now that we have the door changes and the item changes, implement them!
	# first, make the new rom file:
	shutil.copyfile(args.clean, args.create)
	rom_setup(args.create, escape_timer)

	# then make the necessary changes
	make_items(item_changes, args.create)
	make_doors(door_changes, args.clean, args.create)