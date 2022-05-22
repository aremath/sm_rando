import random
import sys
import argparse
import pickle
import glob
from pathlib import Path
from world_rando.coord import Coord, Rect
from world_rando import asp_wave_collapse
from rom_tools.rom_manager import RomManager
from rom_tools import rom_data_structures
from rom_tools import graphics

# If a level is larger than this, it won't be reconfigured, since
# grounding the ASP model will take ages
#TODO
size_threshold = 6000

rom0_path = "../roms/sm_asp.smc"
rom1_path = "../roms/sm_asp_1.smc"
rom2_path = "../roms/sm_asp_2.smc"
rom_clean_path = "../roms/sm_clean.smc"
out_path = Path("output/asp")

# Used for autofilling args from wfc_args
class WFCArgs(object):

    def __init__(self, name, seed=None, extra_similarity=0.02, auto_rect=True, rects=None):
        self.name = name
        # How many extra tiles are constrained, as a percentage of
        # the level
        self.extra_similarity = extra_similarity
        self.auto_rect = auto_rect
        self.rects = rects
        self.seed = seed

    @property
    def tuple(self):
        return (self.auto_rect, self.rects, self.extra_similarity, self.seed)

#TODO: in addition to a ROM, read and write a data structure
# that remembers RNG seed so that you can re-run an individual level
# consistently
wfc_args = [
        # Crateria
        #("room_header_0x791f8",),          # too big
        ("room_header_0x792b3",0),          # done
        ("room_header_0x792fd",0),          # done
        ("room_header_0x793aa",0),          # done
        #("room_header_0x793d5",),          # save station
        #("room_header_0x793fe",),          # too big
        ("room_header_0x79461",0),          # done
        ("room_header_0x7948c",0),          # done
        #("room_header_0x794cc",),          # done elevator
        ("room_header_0x794fd",0),          # done
        ("room_header_0x79552",0, 0.05),    # done
        ("room_header_0x7957d",0, 0.05),    # done, not first try
        ("room_header_0x795a8",0),          # done
        ("room_header_0x795d4",0),          # sometimes creates misplaced doors
        ("room_header_0x795ff",0),          # done
        ("room_header_0x7962a",0),          # done
        ("room_header_0x7965b",0),          # done
        ("room_header_0x7968f",0),          # done
        ("room_header_0x796ba",0),          # done
        ("room_header_0x7975c",0, 0.02),    # more
        ("room_header_0x797b5",0),          # done
        #("room_header_0x79804",),          # bomb torizo
        ("room_header_0x79879",0),          # done
        ("room_header_0x798e2",0),          # done
        ("room_header_0x7990d",0, 0.02, False, None),          # done, terminator disable the usual rect-finding
        ("room_header_0x79938",0),          # done
        ("room_header_0x79969",0),          # done
        #("room_header_0x79994",),          # map station
        ("room_header_0x799bd",0, 0.25),    # done
        #("room_header_0x799f9",),          # too big, TODO: crashing for some reason
        ("room_header_0x79a44",0),          # done
        ("room_header_0x79a90",0),          # done
        # Brinstar
        ("room_header_0x79ad9",0),          # brinstar entrance (more?)
        ("room_header_0x79b5b",0),          # post-spore shaft
        ("room_header_0x79b9d",0),          # pre-map
        ("room_header_0x79bc8",0),          # early supers
        ("room_header_0x79c07",0),          # post-early supers
        #("room_header_0x79c35",),          # map station
        #("room_header_0x79c5e",0),          # brinstar firefleas #TODO
        #("room_header_0x79c89",),          # missile station
        ("room_header_0x79cb3",0),          # dachora
        #("room_header_0x79d19",),          # big pink, too big probably
        ("room_header_0x79d9c",0),          # kihunters
        ("room_header_0x79dc7",0),          # spore spawn
        ("room_header_0x79e11",0),          # mission impossible
        #("room_header_0x79e52",0),          # green hill zone TODO: crashing for some reason
        #("room_header_0x79e9f",0,0.05,False,[Rect(Coord(0,32),Coord(128,48))]),          # morph
                                            #TODO: crashing (context has no solution)
        ("room_header_0x79f11",0,0.1),          # construction zone TODO: weird invisible blocks?
        ("room_header_0x79f64",0),          # post-construction zone
        ("room_header_0x79fba",0),          # noob bridge
        ("room_header_0x79fe5",0),          # crateria beetoms
        ("room_header_0x7a011",0,0.02,False,[Rect(Coord(0,16),Coord(80,32))]),          # crateria super crumble
        #("room_header_0x7a051",),          # crateria supers
        #("room_header_0x7a07b",),          # energy refill
        ("room_header_0x7a0a4",0),          # post-first-supers
        ("room_header_0x7a0d2",0),          # waterway
        #("room_header_0x7a107",0),          # missiles room
        ("room_header_0x7a130",0),          # crateria wave room
        ("room_header_0x7a15b",0),          # crateria wave etank
        #("room_header_0x7a184",),          # save room
        ("room_header_0x7a1ad",0),          # boulders
        #("room_header_0x7a1d8",),          # missiles room
        #("room_header_0x7a201",),          # save room
        #("room_header_0x7a22a",),          # save room
        ("room_header_0x7a253",0),          # red tower
        ("room_header_0x7a293",0),          # x-ray entrance
        ("room_header_0x7a2ce",0),          # x-ray
        ("room_header_0x7a2f7",1),          # hellway
        ("room_header_0x7a322",0),          # caterpillars
        ("room_header_0x7a37c",0),          # beta pbs
        ("room_header_0x7a3ae",0),          # alpha pbs
        ("room_header_0x7a3dd",0),          # bats
        ("room_header_0x7a408",1,0.1),      # pre-spazer very bad
        #("room_header_0x7a447",),          # spazer
        ("room_header_0x7a471",0),          # warehouse 1
        ("room_header_0x7a4b1",0),          # warehouse beetoms
        ("room_header_0x7a4da",0),          # warehouse 2
        ("room_header_0x7a521",0),          # warehouse 3
        ("room_header_0x7a56b",0),         # warehouse 4
        #("room_header_0x7a59f",),          # kraid
        ("room_header_0x7a5ed",0),          # statues entrance
        #("room_header_0x7a618",),          # energy refill
        #("room_header_0x7a641",),          # energy missiles refill
        ("room_header_0x7a66a",0,0),         # statues
        #("room_header_0x7a6a1",),          # statues entrance
        #("room_header_0x7a6e2",),          # varia
        #("room_header_0x7a70b",),          # save room
        #("room_header_0x7a734",),          # save room
        # Norfair
        ("room_header_0x7a75d",0),          # norfair trippers very bad
        ("room_header_0x7a788",0,0),          # cathedral
        ("room_header_0x7a7b3",0,0),          # cathedral entrance
        ("room_header_0x7a7de",0),          # business center
        ("room_header_0x7a815",0),          # ice entrance
        ("room_header_0x7a865",0),          # ice tutorial
        ("room_header_0x7a890",0),          # ice
        ("room_header_0x7a8b9",0),          # ice namihes it's beautiful
        #("room_header_0x7a8f8",1,0),          # crumble shaft #TODO
        ("room_header_0x7a923",0),          # croc entrance
        #("room_header_0x7a98d",),          # croc
        ("room_header_0x7a9e5",0),          # hi jump
        ("room_header_0x7aa0e",0),          # croc escape
        #("room_header_0x7aa41",0),          # pre-hi jump #TODO
        ("room_header_0x7aa82",0),          # post croc
        #("room_header_0x7aab5",),          # save room
        ("room_header_0x7aade",0),          # post croc pbs
        ("room_header_0x7ab07",0),          # violas
        ("room_header_0x7ab3b",0),          # cosine
        #("room_header_0x7ab64",0),          # grapple tutorial 3 #TODO
        #("room_header_0x7ab8f",),          # grapple yump
        ("room_header_0x7abd2",0),          # grapple tutorial 2
        ("room_header_0x7ac00",0),          # grapple tutorial 1
        ("room_header_0x7ac2b",0),          # grapple
        ("room_header_0x7ac5a",0),          # bubble reserve
        #("room_header_0x7ac83",0),          # bubble reserve entrance #TODO
        #("room_header_0x7acb3",0),          # bubble main #TODO
        ("room_header_0x7acf0",0),          # speed entrance
        ("room_header_0x7ad1b",0),          # speed
        #("room_header_0x7ad5e",0),          # single chamber #TODO
        #("room_header_0x7adad",0),          # double chamber #TODO
        ("room_header_0x7adde",0),          # wave
        ("room_header_0x7ae07",0,0.1),          # spiky platforms
        #("room_header_0x7ae32",0),          # volcano room #TODO
        ("room_header_0x7ae74",0),          # kronic boost
        ("room_header_0x7aeb4",0),          # magdollite tunnel
        ("room_header_0x7aedf",0,0.1),          # purple shaft
        ("room_header_0x7af14",0,0.1),          # lava dive | more
        ("room_header_0x7af3f",0),          # lower norfair elevator
        ("room_header_0x7af72",0),          # upper norfair farm
        ("room_header_0x7afa3",0),          # rising tide | more
        ("room_header_0x7afce",0),          # acid snakes
        ("room_header_0x7affb",0),          # spiky acid snakes
        #("room_header_0x7b026",),          # croc refill
        ("room_header_0x7b051",0),          # purple norfair farm
        #("room_header_0x7b07a",0),          # bat cave #TODO
        #("room_header_0x7b0b4",),          # norfair map room
        #("room_header_0x7b0dd",),          # save room
        ("room_header_0x7b106",0),          # frog speedway
        ("room_header_0x7b139",0),          # red pirates shaft
        #("room_header_0x7b167",),          # save room
        #("room_header_0x7b192",),          # save room
        #("room_header_0x7b1bb",),          # save room
        # Lower Norfair
        ("room_header_0x7b1e5",0),          # wc
        ("room_header_0x7b236",0),          # ln elevator
        ("room_header_0x7b283",0),          # gt
        ("room_header_0x7b2da",0),          # rippers
        #("room_header_0x7b305",),          # energy refill
        #("room_header_0x7b32e",),          # ridley
        ("room_header_0x7b37a",0),          # pre-rodney
        ("room_header_0x7b3a5",0),          # golden pirates
        #("room_header_0x7b40a",0),          # mickey mouse #TODO
        ("room_header_0x7b457",0),          # spark
        ("room_header_0x7b482",0),          # plowerhouse
        ("room_header_0x7b4ad",0),          # worst room
        #("room_header_0x7b4e5",0),          # amphitheater #TODO
        ("room_header_0x7b510",0),          # hotarubi
        ("room_header_0x7b55a",0),          # jail
        ("room_header_0x7b585",0),          # red kihunters
        ("room_header_0x7b5d5",0),          # wasteland
        #("room_header_0x7b62b",),          # metal pirates
        ("room_header_0x7b656",0),          # 3 musketeers
        #("room_header_0x7b698",),          # ridley etank
        #("room_header_0x7b6c1",),          # screw
        #("room_header_0x7b6ee",),          # ln firefleas
        #("room_header_0x7b741",),          # save room
        # Wrecked Ship
        #("room_header_0x7c98e",),          # statue twitter room
        #("room_header_0x7ca08",),          # treadmill
        #("room_header_0x7ca52",),          # attic
        #("room_header_0x7caae",),          # beep boop
        #("room_header_0x7caf6",),          # wrecked ship entrance
        #("room_header_0x7cb8b",),          # spiky room
        #("room_header_0x7cbd5",),          # ship water electricity room
        #("room_header_0x7cc6f",),          # basement
        #("room_header_0x7cccb",),          # wrecked ship map
        #("room_header_0x7cd13",),          # phantoon
        #("room_header_0x7cd5c",),          # wrecked ship bull
        #("room_header_0x7cda8",),          # wrecked ship supers a
        #("room_header_0x7cdf1",),          # wrecked ship supers b
        #("room_header_0x7ce40",),          # gravity
        #("room_header_0x7ce8a",),          # wrecked ship save
        # Maridia
        #("room_header_0x7ced2",),          # save point
        #("room_header_0x7cefb",),          # tube
        #("room_header_0x7cf54",),          # one crab
        #("room_header_0x7cf80",),          # post-tube
        #("room_header_0x7cfc9",),          # main street
        #("room_header_0x7d017",),          # main street pink pirates
        #("room_header_0x7d055",),          # mama turtle
        ]

wfc_args = [WFCArgs(*args) for args in wfc_args]

def get_args(arg_list):
    parser = argparse.ArgumentParser(description="Build new rooms for Super Metroid using wavefunction collapse!")
    parser.add_argument("--revert", action="store_true", help="Reset altered rooms to their original state")
    parser.add_argument("--compile", action="store_true", help="Compile the generated rooms from the output folder into a rom")
    args = parser.parse_args(arg_list)
    return args

def get_computed_files():
    return glob.glob(str(out_path / "*.p"))

def revert():
    clean_rom = RomManager(rom_clean_path, "../roms/sm_foo.smc")
    revert_rom = RomManager(rom2_path, rom0_path)
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

def make_data():
    random.seed(0)
    rom = RomManager(rom_clean_path, rom2_path)
    print("Parsing...")
    obj_names = rom.parse()
    print("Collapsing...")
    computed_files = set(get_computed_files())
    for args in wfc_args:
        img_path = out_path / (args.name + "_img.png")
        obj_path = out_path / (args.name + "_obj.p")
        if str(obj_path) in computed_files:
            continue
        print("Creating room {}".format(args.name))
        #print(sameness)
        h = obj_names[args.name]
        # Only leveldata for default state, and fns for producing other leveldata
        level, fns = asp_wave_collapse.wfc_level_data(h, *args.tuple)
        # Make an image
        img = graphics.layer1_image_from_tileset(rom, level[1].layer1, h.state_chooser.default.tileset)
        img.save(img_path)
        # Pickle the level, fns
        with open(obj_path, "wb") as f:
            pickle.dump((args.name, level, fns), f)
        print()
    print("Done!")

def rom_compile():
    print("Parsing...")
    rom = RomManager(rom_clean_path, rom2_path)
    obj_names = rom.parse()
    print("Reading level data...")
    # Find the level data - should be .p files in the output folder
    for obj_path in get_computed_files():
        # Read the data
        with open(obj_path, "rb") as f:
            name, level, fns = pickle.load(f)
            h = obj_names[name]
        asp_wave_collapse.create(h, level, fns)
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
    elif args.compile:
        rom_compile()
    else:
        make_data()
