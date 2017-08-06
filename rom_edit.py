from struct import *

def read_door_data(source, door_addr):
	pass

def write_door_data(door, data):
	pass

# methods for actually writing to / reading from the ROM
# based on the hexMethods.py file from the other sm door randomizer

#TODO: do this without opening and closing the file repeatedly

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
	door data. Creates two dictionaries, from and to. From is indexed by door name
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
