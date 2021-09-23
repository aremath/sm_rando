import random
from world_rando import asp_wave_collapse
from rom_tools.rom_manager import RomManager
from rom_tools import rom_data_structures

header_names = [
        #"room_header_0x792b3",
        "room_header_0x7965b",
        #"room_header_0x799bd",
        #"room_header_0x792fd"
        #"room_header_0x79969"
        ]

#TODO: pickly stuff for more "interactive" where you can
# reload and re-generate rooms

if __name__ == "__main__":
    random.seed(0)
    rom = RomManager("../roms/sm_clean.smc", "../roms/sm_asp.smc")
    print("Parsing...")
    obj_names = rom.parse()
    print("Collapsing...")
    for name in header_names:
        h = obj_names[name]
        asp_wave_collapse.wfc_and_create(h, 0.01)
        print()
    #all_headers = [obj for obj in obj_names.values() if type(obj) is rom_data_structures.RoomHeader]
    #for h in all_headers:
    #    asp_wave_collapse.wfc_and_create(h)
    print("Compiling...")
    rom.compile(obj_names)
    rom.save_and_close()
    print("Done!")

