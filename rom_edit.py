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

def write_raw_bytes(source, offset, byte, length):
    """Writes the byte at the given offset"""
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
	write_raw_bytes(rom_file, replace_door, door, 12)
	