# Author - Aremath
# methods for actually writing to / reading from the ROM
# based on the hexMethods.py file from the other sm door randomizer
#TODO: eventually most of this should be folded into rom_tools

#TODO: what is struct used for??
from struct import *
import collections
import re

from . import item_definitions
from .address import *

#TODO: clean up usage of defns - either remove it or use definitions!

def make_test_rom(rom, offset, direction):
    """Makes a test rom to see what door is at offset"""
    # I want to make either landing site L2 or landing site R2 lead to that door info
    # 04 is left, 05 is right
    replace_door = ""
    if direction == "L":
        # landing site l1
        replace_door = Address(0x001892e)
    elif direction == "R":
        # landing site r2
        replace_door = Address(0x0018922)
    elif direction == "B":
        # parlor b
        replace_door = Address(0x001898e)
    else:
        assert False, "Bad Direction"
    door = rom.read_from_clean(offset, 12)
    rom.write_to_new(replace_door, door)

#TODO: some way to make it easier to put arbitrary bytes in a file...
def parse_patches(patch_file):
    f = open(patch_file, "r")
    patches = []
    for line in f.readlines():
        # Remove whitespace
        line = line.strip()
        # Skip comments
        if line[0] == "#":
            continue
        (memory_address, data) = line.split()
        memory_address = Address(int(memory_address, 16))
        patches.append((memory_address, data))
    f.close()
    return patches

def parse_doors(door_file, rom):
    """Use the door definitions files so that door nodes can be used to access
    door data. Creates two dictionaries, from and to. From is indexed by door names
    and has the memory address for each door. Writing to that memory address will alter
    that door. To is indexed by door name, and contains the door data. Writing this memory
    to another door memory address with make that door lead to the specified door."""
    f = open(door_file, "r")
    # key - door name
    # value - memory address of that door
    door_from = {}
    # key - door name
    # value - data for that door
    door_to = {}
    for line in f.readlines():
        # remove unnecessary characters
        line = line.strip()
        # skip comments
        if line[0] == "#":
            continue
        (d_from, mem_addr, d_to) = line.split()
        mem_addr = Address(int(mem_addr, 16))
        door_from[d_from] = mem_addr
        door_to[d_to] = rom.read_from_clean(mem_addr, 12)
    f.close()
    return door_from, door_to

# As an example, if you use write(door_from["Parlor_L1"], door_to["Crocomire_Speedway_R1"]),
# then heading through Parlor L1 will bring you out at Crocomire Speedway R1.
# The opposite is write(door_from["Crocomire_Speedway_R1"], door_to["Parlor_L1"])

def make_doors(door_list, rom):
    """Make the doors specified by door_list in write_rom, using the memory locations from clean_rom."""
    # door_list is a list of tuples (d1, d2), where d1 and d2 are the names of door nodes.
    # this connects door1 to door2, and vice versa.

    # first, get the door dictionary
    door_from, door_to = parse_doors("encoding/dsl/door_defns.txt", rom)

    for door1, door2 in door_list:
        # special-case the pants room!
        if door1 == "Pants_R1":
            rom.write_to_new(door_from[door1], door_to[door2])
            rom.write_to_new(door_from[door2], door_to["Pants_Right_R"])
            rom.write_to_new(door_from["Pants_Right_R"], door_to[door2])
        elif door2 == "Pants_R1":
            rom.write_to_new(door_from[door2], door_to[door1])
            rom.write_to_new(door_from[door1], door_to["Pants_Right_R"])
            rom.write_to_new(door_from["Pants_Right_R"], door_to[door1])
        else:
            # skip doors that don't exist
            #TODO: only certain TS and BS doors
            if door1 in door_from and door2 in door_to:
                rom.write_to_new(door_from[door1], door_to[door2])
            if door2 in door_from and door1 in door_to:
                rom.write_to_new(door_from[door2], door_to[door1])

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
        memory_address = Address(int(memory_address, 16))
        item_locations[location] = (memory_address, location_type)
    f.close()
    return item_locations

def make_items(item_list, rom):
    """Make the items specified by the item list in write_rom"""
    # item_list is a list of tuples, (location, item) where location is the name of 
    # an item node, and item is the name of an item.
    item_defns = item_definitions.make_item_definitions()
    item_locations = parse_item_locations("encoding/dsl/item_locations.txt")
    for location, item in item_list:
        if location in item_locations:
            address, location_type = item_locations[location]
            rom.write_to_new(address, item_defns[item][location_type])

def parse_saves(save_file):
    f = open(save_file, "r")
    # Key - save room door
    # Value - address of the door data used by that save room
    save_locs = {}
    for line in f.readlines():
        # Remove unnecessary characters
        line = line.strip()
        # Skip comments
        if line[0] == "#":
            continue
        (save_room, save_door, offset) = line.split()
        offset = Address(int(offset, 16))
        save_locs[save_room + "_" + save_door] = offset
    return save_locs

def make_saves(door_changes, rom):
    door_from, _ = parse_doors("encoding/dsl/door_defns.txt", rom)
    # The last 2 bytes comprise the pointer
    door_from = {node: addr.as_snes_bytes(2) for node, addr in door_from.items()}
    save_locs = parse_saves("encoding/dsl/saves.txt")
    for ldoor, rdoor in door_changes:
        if ldoor in save_locs:
            rom.write_to_new(save_locs[ldoor], door_from[rdoor])
        if rdoor in save_locs:
            rom.write_to_new(save_locs[rdoor], door_from[ldoor])

skyscroll = {
    # Landing Site:
    # 8946: Gauntlet_Entrance_R -> Landing_Site_L1
    # $8F:B76A
    # 896A: Parlor_R1 -> Landing_Site_L2
    # $8F:B775
    # 89B2: Crateria_Power_Bombs_L -> Landing_Site_R1
    # $8F:B780
    # 8AC6: Crateria_Tube_L -> Landing_Site_R2
    # $8F:B78B
    # 88FE ?
    # 890A ?
    "Landing_Site_L1": Address(0x8fb76c, mode="snes"),
    "Landing_Site_L2": Address(0x8fb777, mode="snes"),
    "Landing_Site_R1": Address(0x8fb782, mode="snes"),
    "Landing_Site_R2": Address(0x8fb78d, mode="snes"),
    # West Ocean
    # 8A12: Bowling_Path_L -> West_Ocean_R3
    # $8F:B7AE
    # 8AEA: Moat_R -> West_Ocean_L2
    # $8F:B7B9
    # A18C: Bowling_Alley_L1 -> West_Ocean_R2
    # $8F:B7C4
    # A1B0: Wrecked_Ship_Entrance_L -> West_Ocean_R6
    # $8F:B7CF
    # A1E0: Attic_L -> West_Ocean_R1
    # $8F:B7DA
    # A300: Gravity_L -> West_Ocean_R5
    # $8F:B7E5
    "West_Ocean_R3": Address(0x8fb7b0, mode="snes"),
    "West_Ocean_L2": Address(0x8fb7bb, mode="snes"),
    "West_Ocean_R2": Address(0x8fb7c6, mode="snes"),
    "West_Ocean_R6": Address(0x8fb7d1, mode="snes"),
    "West_Ocean_R1": Address(0x8fb7dc, mode="snes"),
    "West_Ocean_R5": Address(0x8fb7e7, mode="snes"),
    # East Ocean
    # 8A7E: Forgotten_Highway_L -> East_Ocean_R
    # $8F:B7F2
    # A264: Electric_Room_of_Death_R -> East_Ocean_L
    # $8F:B7FD
    "East_Ocean_R": Address(0x8fb7f4, mode="snes"),
    "East_Ocean_L": Address(0x8fb7ff, mode="snes"),
        }

def fix_skyscroll(door_changes, rom):
    door_from, _ = parse_doors("encoding/dsl/door_defns.txt", rom)
    # The last 2 bytes comprise the pointer
    door_from = {node: addr.as_snes_bytes(2) for node, addr in door_from.items()}
    for ldoor, rdoor in door_changes:
        if ldoor in skyscroll:
            rom.write_to_new(skyscroll[ldoor], door_from[rdoor])
        if rdoor in skyscroll:
            rom.write_to_new(skyscroll[rdoor], door_from[ldoor])

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
    "E"  : Address(0xb2ce),
    "S"  : Address(0xb2e0),
    "PB" : Address(0xb2e9),
    "M"  : Address(0xb2d7)
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
                print(item_def + " requires an amount!")
        else:
            print(item_def + " is not supported as a starting item!")
    # setup for writing the codes
    rom.write_to_new(Address(0xb2fd), b"\x20\x20\xef")
    rom.write_to_new(Address(0xef20), b"\xA9\x00\x00\x8D\xA2\x09\x8D\xA4\x09\xA9\x00\x00\x8D\xA6\x09\x8D\xA8\x09\x60")
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
    code_bytes = total_code.to_bytes(2, byteorder='little')
    rom.write_to_new(Address(0xef2a), code_bytes)

#TODO: this naming scheme is a little strange
# helper function for make_starting_items
# sets the item bitmask
def make_start_items(items, rom):
    total_code = 0
    for item in items:
        total_code += item_codes[item]
    code_bytes = total_code.to_bytes(2, byteorder='little')
    rom.write_to_new(Address(0xef21), code_bytes)

# helper function for make_starting_items
# sets the starting ammo amounts
def make_start_ammo(ammos, rom):
    # ammos is a list of tuples of (ammo type, amount)
    for ammo_type, ammo_amount in ammos:
        ammo_bytes = ammo_amount.to_bytes(2, byteorder='little')
        rom.write_to_new(ammo_addrs[ammo_type], ammo_bytes)

# Patch to make the item in the old mother brain room appear when zebes is asleep
# offset should be free space in bank 8F
# which starts at PC address 0x7e99a
def make_old_mb_work(offset, rom):
    a_awake = Address(0x8f83d0, mode="snes")
    a_asleep = Address(0x8f83b6, mode="snes")
    item_offset = Address(30)
    # Only copy 18 to remove the grey door
    old_plms = rom.read_from_clean(a_asleep, 18)
    # Read from new in case the item type was changed
    item_plm = rom.read_from_new(a_awake + item_offset, 6)
    new_plms = old_plms + item_plm + b"\x00\x00"
    # Write the PLM set
    rom.write_to_new(offset, new_plms)
    # Write the pointer to the PLM set in the Old MB room header
    ptr = offset.as_snes_bytes(2)
    rom.write_to_new(Address(0x79781), ptr)
    return offset + Address(len(new_plms))

def make_morph_room_work(offset, rom):
    # First the address of the PLM list
    a_awake = Address(0x8f86e6, mode="snes")
    # Then the address of the PLM list pointer
    awake_ptr = Address(0x79edf)
    a_asleep = Address(0x8f867e, mode="snes")
    asleep_ptr = Address(0x79ec5)
    mb_offset = Address(96)
    # Read form new in case the item type was changed
    base_plms = rom.read_from_new(a_awake, 108)
    mb_plm = rom.read_from_new(a_asleep + mb_offset, 6)
    new_plms = base_plms + mb_plm + b"\x00\x00"
    # Write the PLM set
    rom.write_to_new(offset, new_plms)
    # Update the pointers
    ptr = offset.as_snes_bytes(2)
    rom.write_to_new(awake_ptr, ptr)
    rom.write_to_new(asleep_ptr, ptr)
    return offset + Address(len(new_plms))

# Turns crateria map room into a Golden 4 room
# in order to make it easier to find golden 4
def two_g4s(offset, rom):
    g4_ptr = Address(0x7a66a)
    crateria_map_ptr = Address(0x79994)
    # Standard 1-state room header is 39 bytes
    g4_header = rom.read_from_clean(g4_ptr, 39)
    # Write the g4 room header over the crateria map room header
    rom.write_to_new(crateria_map_ptr, g4_header)
    # Create the new door list
    # Door1 is the actual crateria map door
    door1 = Address(0x818c2e, mode="snes")
    # Door2 and Door3 are stolen from G4 and leads to Tourian (extra door for elevator)
    door2 = Address(0x819222, mode="snes")
    door3 = Address(0x8188fc, mode="snes")
    d1b = door1.as_snes_bytes(2)
    d2b = door2.as_snes_bytes(2)
    d3b = door3.as_snes_bytes(2)
    doors = d1b + d2b + d3b
    rom.write_to_new(offset, doors)
    # Write the pointer to the new doors inside the header
    doors_ptr_loc = Address(0x7999d)
    doors_ptr = offset.as_snes_bytes(2)
    rom.write_to_new(doors_ptr_loc, doors_ptr)
    return offset + Address(len(doors))

# Catchall to apply small changes to the ROM that have to do with making the various logical changes work
def logic_improvements(rom, g4):
    # Free space in bank 8f
    free_8f = Address(0x7e99a)
    max_8f = Address(0x80000)
    free_8f = make_old_mb_work(free_8f, rom)
    assert free_8f < max_8f
    free_8f = make_morph_room_work(free_8f, rom)
    assert free_8f < max_8f
    if g4:
        free_8f = two_g4s(free_8f, rom)
        assert free_8f < max_8f

