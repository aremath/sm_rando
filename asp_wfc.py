import random
import sys
import argparse
from world_rando import asp_wave_collapse
from rom_tools.rom_manager import RomManager
from rom_tools import rom_data_structures

# On average, how many extra tiles are constrained, as a percentage of
# the level
#TODO: try to distribute these tiles evenly throughout the level?
default_sameness = 0.02
# If a level is larger than this, it won't be reconfigured, since
# grounding the ASP model will take ages
#TODO
size_threshold = 6000

rom0_path = "../roms/sm_asp.smc"
rom1_path = "../roms/sm_asp_1.smc"
rom_clean_path = "../roms/sm_clean.smc"


#TODO: reverting

header_names = [
        # Crateria
        #"room_header_0x791f8",          # too big
        #"room_header_0x792fd",          # too big
        #"room_header_0x792b3",          # done
        #"room_header_0x793aa",          # done
        #"room_header_0x793d5",          # save station
        #"room_header_0x793fe",          # too big
        #"room_header_0x79461",          # done
        #"room_header_0x7948c",          # done #TODO: layer2?
        #"room_header_0x794cc",          # done #TODO: layer2?
        #"room_header_0x794fd",          # too big
        #("room_header_0x79552", 0.05),   # done
        #"room_header_0x7957d",          #           more
        #"room_header_0x795a8",          # done
        #"room_header_0x795d4",          # done #TODO: layer2?
        #"room_header_0x795ff",          # done
        #"room_header_0x7962a",          # done #TODO: layer2?
        #"room_header_0x7965b",          # done
        #"room_header_0x7968f",          # done layer2
        #"room_header_0x796ba",          # too big
        #("room_header_0x7975c", 0.3),   #           more
        #"room_header_0x797b5",          # done layer2
        #"room_header_0x79804",          # bomb torizo
        #"room_header_0x79879",          # done
        #"room_header_0x798e2",          # done
        #"room_header_0x7990d",          # done
        #"room_header_0x79938",          # done layer2
        #"room_header_0x79969",          # done
        #"room_header_0x79994",          # map station
        #("room_header_0x799bd", 0.3),   # done
        #"room_header_0x799f9",          # too big
        #"room_header_0x79a44",          # done
        #"room_header_0x79a90",          # done
        # Brinstar
        ]

def get_args(arg_list):
    parser = argparse.ArgumentParser(description="Build new rooms for Super Metroid using wavefunction collapse!")
    parser.add_argument("--revert", action="store_true", help="Reset altered rooms to their original state")
    args = parser.parse_args(arg_list)
    return args

def revert():
    clean_rom = RomManager(rom_clean_path, "../roms/sm_foo.smc")
    revert_rom = RomManager(rom1_path, rom0_path)
    print("Parsing...")
    clean_names = clean_rom.parse()
    revert_names = revert_rom.parse()
    print("Resetting rooms...")
    for name in header_names:
        if len(name) == 2:
            name, sameness = name
        clean_states = clean_names[name].all_states()
        revert_states = revert_names[name].all_states()
        for (clean_state, revert_state) in zip(clean_states, revert_states):
            print(clean_state.name)
            clean_level = clean_state.level_data
            revert_level = revert_state.level_data
            #TODO: this will allocate the new level in a different location (potentially multiple times)
            c_level = revert_names.create(type(clean_state.level_data), *clean_level.list, replace=revert_level)
            revert_state.level_data = c_level.name
    print("Compiling...")
    revert_rom.compile(revert_names)
    revert_rom.save_and_close()
    print("Done!")

def make_new():
    random.seed(0)
    rom = RomManager(rom_clean_path, rom1_path)
    #rom = RomManager(rom0_path, rom1_path)
    print("Parsing...")
    obj_names = rom.parse()
    print("Collapsing...")
    for name in header_names:
        if len(name) == 2:
            name, sameness = name
        else:
            sameness = default_sameness
        #print(sameness)
        h = obj_names[name]
        asp_wave_collapse.wfc_and_create(h, sameness)
        #asp_wave_collapse.wfc_and_create(h, 1)
        print()
    #all_headers = [obj for obj in obj_names.values() if type(obj) is rom_data_structures.RoomHeader]
    #for h in all_headers:
    #    asp_wave_collapse.wfc_and_create(h)
    print("Compiling...")
    rom.compile(obj_names)
    rom.save_and_close()
    print("Done!")


#TODO: pickly stuff for more "interactive" where you can
# reload and re-generate rooms

if __name__ == "__main__":
    args = get_args(sys.argv[1:])
    if args.revert:
        revert()
    else:
        make_new()
