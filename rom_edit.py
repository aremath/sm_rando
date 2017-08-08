from struct import *
import collections
import item_definitions

# methods for actually writing to / reading from the ROM
# based on the hexMethods.py file from the other sm door randomizer

#TODO: do this without opening and closing the file repeatedly
#TODO: clean up usage of defns - either remove it or use definitions!

def read_bytes(source, offset, length):
    """Gets length bytes from the given offset"""
    data = open(source, "rb")
    currLoc = int(offset,0)
    data.seek(currLoc)
    currRead = data.read(length)
    data.close()
    array = unpack("B" * length, currRead)
    return array_to_bytes(array)

def read_raw_bytes(source, offset, length):
    """Gets the length bytes from the given offset"""
    data = open(source, "rb")
    currLoc = int(offset,0)
    data.seek(currLoc)
    result = data.read(length)
    data.close()
    return result

def write_raw_bytes(source, offset, byte):
    """Writes the byte at the given offset, overwriting the memory that was there."""
    data = open(source, "r+b")
    currLoc = int(offset,0)
    data.seek(currLoc)
    data.write(byte)
    data.close()

def array_to_bytes(array):
    """Converts an array of integers to bytes"""
    word = ""
    for num in array:
        current_byte = hex(num)[2:]
        if len(current_byte) < 2:
            current_byte = "0" + current_byte
        word = current_byte + word
    return "0x" + word

def make_test_rom(rom_file, offset, direction):
	"""Makes a test rom to see what door is at offset"""
	# I want to make either landing site L2 or landing site R2 lead to that door info
	# 04 is left, 05 is right
	replace_door = ""
	if direction == "L":
		# landing site l1
		replace_door = "0x001892e"
	elif direction == "R":
		# landing site r2
		replace_door = "0x0018922"
	elif direction == "B":
		# parlor b
		replace_door = "0x001898e"
	else:
		assert False, "Bad Direction"

	door = read_raw_bytes(rom_file, offset, 12)
	write_raw_bytes(rom_file, replace_door, door)
	

def parse_doors(door_file, clean_rom):
	"""Use the door definitions files so that door nodes can be used to acces
	door data. Creates two dictionaries, from and to. From is indexed by door names
	and has the memory address for each door. Writing to that memory address will alter
	that door. To is indexed by door name, and contains the door data. Writing this memory
	to another door memory address with make that door lead to the specified door."""
	f = open(door_file, "r")
	# key - door name
	# value - memory address to write to to affect that door
	door_from = {}
	# key - door name
	# value - data to write to connect a door to that door
	door_to = {}

	for line in f.readlines():
		# remove unnecessary characters
		line = line.strip()
		# skip comments
		if line[0] == "#":
			continue
		(d_from, mem_addr, d_to) = line.split()
		door_from[d_from] = mem_addr
		door_to[d_to] = read_raw_bytes(clean_rom, mem_addr, 12)

	return door_from, door_to

# as an example, if you use write_raw_bytes("example.smc", door_from["Parlor_L1"], door_to["Crocomire_Speedway_R1"]),
# then heading through Parlor L1 will bring you out at Crocomire Speedway R1. Note that to also get the reverse, you must
# write_raw_bytes("example.smc", door_from["Crocomire_Speedway_R1"], door_to["Parlor_L1"])

def make_doors(door_list, clean_rom, write_rom):
	"""Make the doors specified by door_list in write_rom, using the memory locations from clean_rom."""
	# door_list is a list of tuples (d1, d2), where d1 and d2 are the names of door nodes.
	# this connects door1 to door2, and vice versa.

	# first, get the door dictionary
	door_from, door_to = parse_doors("encoding/door_defns.txt", clean_rom)

	for door1, door2 in door_list:
		# special-case the pants room!
		# TODO: this didn't quite work...
		if door1 == "Pants_R":
			write_raw_bytes(write_rom, door_from[door1], door_to[door2])
			write_raw_bytes(write_rom, door_from[door2], door_to["Pants_Right_R"])
		elif door2 == "Pants_R":
			write_raw_bytes(write_rom, door_from[door2], door_to[door1])
			write_raw_bytes(write_rom, door_from[door1], door_to["Pants_Right_R"])
		else:
			# skip doors that don't exist
			#TODO: only certain TS and BS doors
			if door1 in door_from and door2 in door_to:
				write_raw_bytes(write_rom, door_from[door1], door_to[door2])
			if door2 in door_from and door1 in door_to:
				write_raw_bytes(write_rom, door_from[door2], door_to[door1])

"""
def parse_item_defns(item_definitions_file):
	f = open(item_definitions_file, "r")
	# key1 - item type (M, S, SJ, SA, etc.)
	# key2 - location type ((N)ormal, (C)hozo, (H)idden)
	# value - item memory to write to get that item
	item_defs = collections.defaultdict(dict)
	for line in f.readlines():
		# remove junk
		line = line.strip()
		# skip comments
		if line[0] == "#":
			continue
		(item_type, n_item, c_item, h_item) = line.split()
		item_defs[item_type]["N"] = exec(n_item)
		item_defs[item_type]["C"] = exec(c_item)
		item_defs[item_type]["H"] = exec(h_item)
	return item_defs
"""

def parse_item_locations(item_locations_file):
	f = open(item_locations_file)
	# key - item node name
	# value - (memory_address, location_type)
	item_locations = {}
	for line in f.readlines():
		line = line.strip()
		if line[0] == "#":
			continue
		(location, memory_address, location_type) = line.split()
		item_locations[location] = (memory_address, location_type)
	return item_locations


def make_items(item_list, write_rom):
	"""Make the items specified by the item list in write_rom"""
	# item_list is a list of tuples, (location, item) where location is the name of 
	# an item node, and item is the name of an item.
	item_defns = item_definitions.make_item_definitions()
	item_locations = parse_item_locations("encoding/item_locations.txt")
	for location, item in item_list:
		address, location_type = item_locations[location]
		write_raw_bytes(write_rom, address, item_defns[item][location_type])
