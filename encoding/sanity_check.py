from parse_rooms import *
from rom_edit import *

if __name__ == "__main__":
	rooms = parse_rooms("encoding/rooms.txt")
	doors_from, doors_to = parse_doors("encoding/door_defns.txt", "../sm_guinea_pig_copy.smc")

	room_door_list = []

	for room in rooms.values():
		for direction, dir_doors in room[1].items():
			for door in dir_doors:
				room_door_list.append(door)
				if direction != "TS" and direction != "BS":
					if door not in doors_from or door not in doors_to:
						print door

	for door in doors_from:
		if door not in room_door_list:
			print door
