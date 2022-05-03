import random
import sys
import argparse
from world_rando.coord import Coord, Rect
from world_rando import asp_wave_collapse
from rom_tools.rom_manager import RomManager
from rom_tools import rom_data_structures

# If a level is larger than this, it won't be reconfigured, since
# grounding the ASP model will take ages
#TODO
size_threshold = 6000

rom0_path = "../roms/sm_asp.smc"
rom1_path = "../roms/sm_asp_1.smc"
rom_clean_path = "../roms/sm_clean.smc"


# Used for autofilling args from wfc_args
class WFCArgs(object):

    def __init__(self, name, extra_similarity=0.02, auto_rect=True, rects=None):
        self.name = name
        # How many extra tiles are constrained, as a percentage of
        # the level
        self.extra_similarity = extra_similarity
        self.auto_rect = auto_rect
        self.rects = rects

    @property
    def tuple(self):
        return (self.auto_rect, self.rects, self.extra_similarity)

#TODO: in addition to a ROM, read and write a data structure
# that remembers RNG seed so that you can re-run an individual level
# consistently
wfc_args = [
        # Crateria
        #("room_header_0x791f8",),          # too big
        #("room_header_0x792b3",),          # done
        #("room_header_0x792fd",),          # done
        #("room_header_0x793aa",),          # done
        #("room_header_0x793d5",),          # save station
        #("room_header_0x793fe",),          # too big
        #("room_header_0x79461",),          # done
        #("room_header_0x7948c",),          # done
        #("room_header_0x794cc",),          # done
        #("room_header_0x794fd",),          # done
        #("room_header_0x79552", 0.05),     # done
        #("room_header_0x7957d",0.05),      # done, not first try
        #("room_header_0x795a8",),          # done
        #("room_header_0x795d4",),          # sometimes creates misplaced doors
        #("room_header_0x795ff",),          # done
        #("room_header_0x7962a",),          # done
        #("room_header_0x7965b",),          # done
        #("room_header_0x7968f",),          # done
        #("room_header_0x796ba",),          # done
        #("room_header_0x7975c", 0.02),     # more
        #("room_header_0x797b5",),          # done
        #("room_header_0x79804",),          # bomb torizo
        #("room_header_0x79879",),          # done
        #("room_header_0x798e2",),          # done
        #("room_header_0x7990d", 0.02, False, None),          # done, terminator disable the usual rect-finding
        #("room_header_0x79938",),          # done
        #("room_header_0x79969",),          # done
        #("room_header_0x79994",),          # map station
        #("room_header_0x799bd", 0.25),   # done
        #("room_header_0x799f9",),          # too big, TODO: crashing for some reason
        #("room_header_0x79a44",),          # done
        #("room_header_0x79a90",),          # done
        # Brinstar
        #("room_header_0x79ad9",),          # brinstar entrance (more?)
        #("room_header_0x79b5b",),          # post-spore shaft
        #("room_header_0x79b9d",),          # pre-map
        #("room_header_0x79bc8",),          # early supers
        #("room_header_0x79c07",),          # post-early supers
        #("room_header_0x79c35",),          # map station
        #("room_header_0x79c5e",),          # brinstar firefleas
        #("room_header_0x79c89",),          # missile station
        #("room_header_0x79cb3",),          # dachora
        #("room_header_0x79d19",),          # big pink, too big probably
        #("room_header_0x79d9c",),          # kihunters
        #("room_header_0x79dc7",),          # spore spawn
        #("room_header_0x79e11",),          # mission impossible
        #("room_header_0x79e52",),          # green hill zone TODO: crashing for some reason
        #("room_header_0x79e9f",0.02,False,[Rect(Coord(0,32),Coord(128,48))]),          # morph
                                            #TODO: crashing (context has no solution)
        #("room_header_0x79f11",0.1),          # construction zone TODO: weird invisible blocks?
        #("room_header_0x79f64",),          # post-construction zone
        #("room_header_0x79fba",),          # noob bridge
        #("room_header_0x79fe5",),          # crateria beetoms
        #("room_header_0x7a011",0.02,False,[Rect(Coord(0,16),Coord(80,32))]),          # crateria super crumble
        #("room_header_0x7a051",),          # crateria supers
        #("room_header_0x7a07b",),          # energy refill
        #("room_header_0x7a0a4",),          # post-first-supers
        #("room_header_0x7a0d2",),          # waterway
        #("room_header_0x7a107",),          # missiles room
        #("room_header_0x7a130",),          # crateria wave room
        #("room_header_0x7a15b",),          # crateria wave etank
        #("room_header_0x7a184",),          # save room
        #("room_header_0x7a1ad",),          # boulders
        #("room_header_0x7a1d8",),          # missiles room
        #("room_header_0x7a201",),          # save room
        #("room_header_0x7a22a",),          # save room
        #("room_header_0x7a253",),          # red tower
        #("room_header_0x7a293",),          # x-ray entrance
        #("room_header_0x7a2ce",),          # x-ray
        #("room_header_0x7a2f7",),          # hellway
        #("room_header_0x7a322",),          # caterpillars
        #("room_header_0x7a37c",),          # beta pbs
        #("room_header_0x7a3ae",),          # alpha pbs
        #("room_header_0x7a3dd",),          # bats
        #("room_header_0x7a408",0.1),       # pre-spazer very bad
        #("room_header_0x7a447",),          # spazer
        #("room_header_0x7a471",),          # warehouse 1
        #("room_header_0x7a4b1",),          # warehouse beetoms
        #("room_header_0x7a4da",),          # warehouse 2
        #("room_header_0x7a521",),          # warehouse 3
        #("room_header_0x7a56b",0),         # warehouse 4
        #("room_header_0x7a59f",),          # kraid
        #("room_header_0x7a5ed",),          # statues entrance
        #("room_header_0x7a618",),          # energy refill
        #("room_header_0x7a641",),          # energy missiles refill
        #("room_header_0x7a66a",0),         # statues
        #("room_header_0x7a6a1",),          # statues entrance
        #("room_header_0x7a6e2",),          # varia
        #("room_header_0x7a70b",),          # save room
        #("room_header_0x7a734",),          # save room
        # Norfair
        #("room_header_0x7a75d",),          # norfair trippers very bad
        #("room_header_0x7a788",0),          # cathedral
        #("room_header_0x7a7b3",0),          # cathedral entrance
        #("room_header_0x7a7de",),          # business center
        #("room_header_0x7a815",),          # ice entrance
        #("room_header_0x7a865",),          # ice tutorial
        #("room_header_0x7a890",),          # ice
        #("room_header_0x7a8b9",),          # ice namihes it's beautiful
        #("room_header_0x7a8f8",),          # crumble shaft
        #("room_header_0x7a923",),          # croc entrance
        #("room_header_0x7a98d",),          # croc
        #("room_header_0x7a9e5",),          # hi jump
        #("room_header_0x7aa0e",),          # croc escape
        #("room_header_0x7aa41",),          # pre-hi jump
        #("room_header_0x7aa82",),          # post croc
        #("room_header_0x7aab5",),          # save room
        #("room_header_0x7aade",),          # post croc pbs
        #("room_header_0x7ab07",),          # violas
        #("room_header_0x7ab3b",),          # cosine
        #("room_header_0x7ab64",),          # grapple tutorial 3
        #("room_header_0x7ab8f",),          # grapple yump
        #("room_header_0x7abd2",),          # grapple tutorial 2
        #("room_header_0x7ac00",),          # grapple tutorial 1
        #("room_header_0x7ac2b",),          # grapple
        #("room_header_0x7ac5a",),          # bubble reserve
        #("room_header_0x7ac83",),          # bubble reserve entrance
        #("room_header_0x7acb3",),          # bubble main
        #("room_header_0x7acf0",),          # speed entrance
        #("room_header_0x7ad1b",),          # speed
        #("room_header_0x7ad5e",),          # single chamber
        #("room_header_0x7adad",),          # double chamber
        #("room_header_0x7adde",),          # wave
        #("room_header_0x7ae07",),          # spiky platforms
        #("room_header_0x7ae32",),          # volcano room
        #("room_header_0x7ae74",),          # kronic boost
        #("room_header_0x7aeb4",),          # magdollite tunnel
        #("room_header_0x7aedf",),          # purple shaft
        #("room_header_0x7af14",),          # lava dive | more
        #("room_header_0x7af3f",),          # lower norfair elevator
        #("room_header_0x7af72",),          # upper norfair farm
        #("room_header_0x7afa3",),          # rising tide | more
        #("room_header_0x7afce",),          # acid snakes
        #("room_header_0x7affb",),          # spiky acid snakes
        #("room_header_0x7b026",),          # croc refill
        #("room_header_0x7b051",),          # purple norfair farm
        #("room_header_0x7b07a",),          # bat cave
        #("room_header_0x7b0b4",),          # norfair map room
        #("room_header_0x7b0dd",),          # save room
        #("room_header_0x7b106",),          # frog speedway
        #("room_header_0x7b139",),          # red pirates shaft
        #("room_header_0x7b167",),          # save room
        #("room_header_0x7b192",),          # save room
        #("room_header_0x7b1bb",),          # save room
        # Lower Norfair
        ]

wfc_args = [WFCArgs(*args) for args in wfc_args]

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
    # Reverted ROM should have the same /pattern/ of names as existing
    name_mapping = {}
    for args in wfc_args:
        name = args.name
        clean_states = clean_names[name].all_states()
        revert_states = revert_names[name].all_states()
        for (clean_state, revert_state) in zip(clean_states, revert_states):
            clean_level = clean_state.level_data
            revert_level = revert_state.level_data
            if clean_level.name in name_mapping:
                revert_level.level_data = name_mapping[clean_level.name]
            else:
                c_level = revert_names.create(type(clean_state.level_data), *clean_level.list, replace=revert_level)
                revert_state.level_data = c_level.name
                name_mapping[clean_level.name] = c_level.name
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
    for args in wfc_args:
        print("Creating room {}".format(args.name))
        #print(sameness)
        h = obj_names[args.name]
        asp_wave_collapse.wfc_and_create(h, *args.tuple)
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
