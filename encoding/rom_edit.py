# Author - Aremath
# methods for actually writing to / reading from the ROM
# based on the hexMethods.py file from the other sm door randomizer

from struct import *
import collections
import item_definitions
import re

#TODO: do this without opening and closing the file repeatedly
#TODO: clean up usage of defns - either remove it or use definitions!
#TODO: byte strings?

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
    door_from, door_to = parse_doors("encoding/dsl/door_defns.txt", clean_rom)

    for door1, door2 in door_list:
        # special-case the pants room!
        if door1 == "Pants_R1":
            write_raw_bytes(write_rom, door_from[door1], door_to[door2])
            write_raw_bytes(write_rom, door_from[door2], door_to["Pants_Right_R"])
            write_raw_bytes(write_rom, door_from["Pants_Right_R"], door_to[door2])
        elif door2 == "Pants_R1":
            write_raw_bytes(write_rom, door_from[door2], door_to[door1])
            write_raw_bytes(write_rom, door_from[door1], door_to["Pants_Right_R"])
            write_raw_bytes(write_rom, door_from["Pants_Right_R"], door_to[door1])
        else:
            # skip doors that don't exist
            #TODO: only certain TS and BS doors
            if door1 in door_from and door2 in door_to:
                write_raw_bytes(write_rom, door_from[door1], door_to[door2])
            if door2 in door_from and door1 in door_to:
                write_raw_bytes(write_rom, door_from[door2], door_to[door1])

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
    item_locations = parse_item_locations("encoding/dsl/item_locations.txt")
    for location, item in item_list:
        if location in item_locations:
            address, location_type = item_locations[location]
            write_raw_bytes(write_rom, address, item_defns[item][location_type])

def parse_saves(save_file):
    f = open(save_file, "r")
    # key -
    # value -
    save_locs = {}

    for line in f.readlines():
        # remove unnecessary characters
        line = line.strip()
        # skip comments
        if line[0] == "#":
            continue
        (save_room, save_door, offset) = line.split()
        save_locs[save_room + "_" + save_door] = offset

    return save_locs

def make_saves(door_changes, clean_rom, write_rom):
    door_from, _ = parse_doors("encoding/dsl/door_defns.txt", clean_rom)
    # the last 4 characters comprise the pointer
    door_from = {node: addr[-4:] for node, addr in door_from.items()}
    # now convert to bytes
    door_from = {node: int_to_hex(int(addr, base=16))[::-1] for node, addr in door_from.items()}
    save_locs = parse_saves("encoding/dsl/saves.txt")
    for ldoor, rdoor in door_changes:
        if ldoor in save_locs:
            write_raw_bytes(write_rom, save_locs[ldoor], door_from[rdoor])
        if rdoor in save_locs:
            write_raw_bytes(write_rom, save_locs[rdoor], door_from[ldoor])

# applying patches!
def apply_patches(patches, write_rom):
    """patches in the simple form of a list of address, bytes pairs"""
    for address, data in patches:
        write_raw_bytes(write_rom, address, data)

#TODO: credit to the item_randomzer for this function....
#TODO: does theirs parse the file in the same way? little vs. big - endian?
#TODO: seems like this is working!
# seems like the .ips format is:
# 3 bytes of address
# 2 bytes of length
# <length> bytes of data to write at that address
# repeat
def apply_ips(ips_file, write_rom, offset=5):
    """applies an IPS patch to write_rom"""
    # list of tuples of the form (address, bytes)
    # where address is the address in the rom file, and bytes is the bytes to
    # write there.
    bytes_to_write = []
    ips_address = ""
    while True:
        # get bytes from the (possibly new) offset
        ips_address = read_raw_bytes(ips_file, hex(offset), 3)
        # this is the ips end code - we're done
        if ips_address == "\x45\x4f\x46":
            break
        ips_length = read_raw_bytes(ips_file, hex(offset + 3), 2)

        # convert to numbers
        true_address = hex_to_int(ips_address)
        true_length = hex_to_int(ips_length)

        # update offset past the end of the bytes we just read
        offset += 5

        # 0000 is the code for - get a new length, then write one byte that many times
        if true_length == 0:
            new_ips_length = read_raw_bytes(ips_file, hex(offset), 2)
            new_true_length = hex_to_int(new_ips_length)
            data = read_raw_bytes(ips_file, hex(offset + 2), 1) * new_true_length
            bytes_to_write.append((hex(true_address), data))
            offset += 3
        # get length bytes at offset, and add them to the write list
        else:
            data = read_raw_bytes(ips_file, hex(offset), true_length)
            bytes_to_write.append((hex(true_address), data))
            offset += true_length

    # write the data
    for address, data in bytes_to_write:
        write_raw_bytes(write_rom, address, data)

# utilities for messing with hex integers

def hex_to_int(hex_string):
    """converts a string of hex bytes to an integer - little-endian"""
    base = 8 * (len(hex_string) - 1)
    converted = 0
    for char in hex_string:
        converted += int(char.encode("hex"), 16) << base
        base -= 8
    return converted

def int_to_hex(convert_int):
    """converts an into to a string of hex bytes - little-endian"""
    # get the number as a hex string
    hex_str = "%x" % convert_int
    # pad with zeroes so even length - necessary to use decode
    padded_hex_str = ("0" * (len(hex_str) % 2)) + hex_str
    # decode it to a byte (or set of bytes)
    return padded_hex_str.decode("hex")

# pay attention to endianness
# key - item name
# value - item byte code for starting the game with that item
#TODO: what about missiles?
item_codes = {
    "B"      : 0x1000,
    "SPB"    : 0x0002,
    "G"      : 0x4000,
    "SA"     : 0x0008,
    "V"      : 0x0001,
    "GS"     : 0x0020,
    "SB"     : 0x2000,
    "HJ"     : 0x0100,
    "SJ"     : 0x0200,
    "MB"     : 0x0004,
    "XR"     : 0x8000
}

# key - item name
# value - item byte code for starting with that beam
beam_codes = {
    "WB"     : 0x0001,
    "IB"     : 0x0002,
    "Spazer" : 0x0004,
    "PLB"    : 0x0008,
    "CB"     : 0x1000
}

# key - item name
# value - address to write the amount of ammo
ammo_addrs = {
    "E"  : "0xB2CE",
    "S"  : "0xB2E0",
    "PB" : "0xB2E9"
}

# takes an item definition as a string
# parses it to make samus start with those items
def make_starting_items(items, rom):
    beam_list = []
    item_list = []
    ammo_list = []
    items = items.split()
    for item in items:
        item_def = item.rstrip("1234567890")
        int_match = re.search("\d+$", item)
        item_n = None
        if int_match is not None:
            item_n = int(int_match.group(0))
        # special case for ammo things
        if item_def in item_codes:
            item_list.append(item_def)
        elif item_def in beam_codes:
            beam_list.append(item_def)
        elif item_def in ammo_addrs:
            if item_n is not None:
                ammo_list.append((item_def, item_n))
            else:
                print item_def + " requires an amount!"
        else:
            print item_def + " is not supported as a starting item!"
    # setup for writing the codes
    write_raw_bytes(rom, "0xB2FD", "\x20\x20\xEF")
    write_raw_bytes(rom, "0xEF20", "\xA9\x00\x00\x8D\xA2\x09\x8D\xA4\x09\xA9\x00\x00\x8D\xA6\x09\x8D\xA8\x09\x60")
    make_start_beams(beam_list, rom)
    make_start_items(item_list, rom)
    make_start_ammo(ammo_list, rom)

# helper function for make_starting_items
# sets the beam bitmask
def make_start_beams(beams, rom):
    # beams is a list of str which indicates what beams to start with
    total_code = 0
    for beam in beams:
        total_code += beam_codes[beam]
    code_bytes = int_to_hex(total_code)
    if len(code_bytes) == 1:
        code_bytes = "\x00" + code_bytes
    assert len(code_bytes) == 2 # the code is only two bytes
    write_raw_bytes(rom, "0xEF2A", code_bytes[::-1]) # reverse code_bytes to get big-endian

#TODO: this naming scheme is a little strange
# helper function for make_starting_items
# sets the item bitmask
def make_start_items(items, rom):
    total_code = 0
    for item in items:
        total_code += item_codes[item]
    code_bytes = int_to_hex(total_code)
    if len(code_bytes) == 1:
        code_bytes = "\x00" + code_bytes
    assert len(code_bytes) == 2
    write_raw_bytes(rom, "0xEF21", code_bytes[::-1])

# helper function for make_starting_items
# sets the starting ammo amounts
def make_start_ammo(ammos, rom):
    # ammos is a list of tuples of (ammo type, amount)
    for ammo_type, ammo_amount in ammos:
        ammo_bytes = int_to_hex(ammo_amount)
        #assert len(ammo_bytes) == 1
        write_raw_bytes(rom, ammo_addrs[ammo_type], ammo_bytes[::-1])

