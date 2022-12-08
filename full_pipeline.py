import random
from world_rando import generate
#from world_rando.settings import default_settings, small_settings, tiny_settings
from world_rando.settings import tiny_settings as s
from rom_tools.rom_manager import RomManager
from world_rando.room_dtypes import convert_rooms

if __name__ == "__main__":
    random.seed(0)
    abstract_map_info = generate.generate_abstract_map(s)
    concrete_map_info = generate.generate_concrete_map(s, abstract_map_info)
    generate.visualize_concrete_maps(concrete_map_info)
    generate.print_stats(concrete_map_info[-1])
    room_info = generate.generate_rooms(s, concrete_map_info)
    generate.visualize_rooms(room_info)
    rom_m = RomManager("../roms/sm_clean.smc", "../roms/sm_generate.smc")
    print("Parsing original rooms")
    parsed_rooms = rom_m.parse()
    new_obj_names = generate.reify_rooms(room_info, parsed_rooms)
    print("Compiling rooms")
    rom_m.compile(new_obj_names)
    rom_m.save_and_close()
    with open("output/mdb.txt") as f:
        f.write(new_obj_names.mdb)

