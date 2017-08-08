from parse_rooms import *
from rom_edit import *

import random
import argparse
import shutil
import sys

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Welcome to the Super Metroid Door randomizer!")
	parser.add_argument("--clean", metavar="<filename>", required=True, help="The path to a clean rom file from the current directory.")
	parser.add_argument("--create", metavar="<filename>", required=True, help="The path to the rom file you want to create.")
	parser.add_argument("--seed", metavar="<seed>", required=False, help="The seed you want to use for the RNG.")

	args = parser.parse_args()

	seed = args.seed
	if seed is None:
		seed = random.randrange(sys.maxsize)
		random.seed(seed)
	random.seed(seed)
	print "RNG SEED - " + str(seed)

	# setup
	rooms = parse_rooms("encoding/rooms.txt")

	landing_site = rooms.pop("Landing_Site")
	current_graph = landing_site[0].graph
	current_exits = landing_site[1]

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
	rooms.pop("Statues")
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
	rooms.pop("Escape_4")
	rooms.pop("Tourian_Save")

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
			door_changes.append((door, other_door))
			current_exits[direction].remove(door)
			current_exits[door_hookups[direction]].remove(other_door)

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
					direction_door = random.choice(room_doors[room_direction])
					# find a match!
					if len(current_exits[door_hookups[room_direction]]) != 0:
						exit = random.choice(current_exits[door_hookups[room_direction]])
						# link the two exits - remove the two doors we linked
						current_exits[door_hookups[room_direction]].remove(exit)
						for sdirection, sdoors in room_doors.items():
							for sdoor in sdoors:
								if sdoor != direction_door:
									current_exits[sdirection].append(sdoor)
						#TODO: add that change to the graph
						# shuffle the items
						for item_node in rooms[rooms_to_place[index]][2]:
							#TODO: add that change to the graph
							new_item = items_to_place.pop()
							item_changes.append((item_node, new_item))

						door_changes.append((exit, direction_door))
						found = index
						break
				if found >= 0:
					break
			# we placed the room at index - remove it
			rooms_to_place.pop(found)
		#print sum([len(dir_doors) for dir_doors in current_exits.values()])

	# now that we have the door changes and the item changes, implement them!
	# first, make the new rom file:
	shutil.copyfile(args.clean, args.create)
	#print item_changes
	#print door_changes
	print "ROOMS NOT PLACED - " + str(len(rooms_to_place))

	make_items(item_changes, args.create)
	make_doors(door_changes, args.clean, args.create)