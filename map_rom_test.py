import random
from world_rando import generate
from world_rando.settings import default_settings, small_settings
from world_rando import map_viz
from rom_tools import rom_manager

if __name__ == "__main__":
    #sets = default_settings
    sets = small_settings
    random.seed(0)
    abstract_map_info = generate.generate_abstract_map(sets)
    concrete_map_info = generate.generate_concrete_map(sets, abstract_map_info)
    rcmaps, _, _, _, extra_info = concrete_map_info
    npaths, path_length, ntiles, room_dims = extra_info
    generate.plot_room_dims(room_dims)

    # Ordinary output
    generate.print_stats(extra_info)
    generate.visualize_abstract_maps(abstract_map_info)
    generate.visualize_concrete_maps(concrete_map_info)
    generate.mission_embeddings(concrete_map_info, abstract_map_info)

    rom = rom_manager.RomManager("../roms/sm_clean.smc", "../roms/sm_map_edit.smc")
    # Put each map on the ROM
    for region, rcmap in rcmaps.items():
        hidden, tiles = rom_manager.region_map_locs[region]
        tmap = map_viz.tiles_parse("encoding/dsl/tiles.txt")
        rcmap_ts = map_viz.cmap_to_tuples(rcmap, tmap) #TODO: negative numbers?
        rom.place_cmap(rcmap_ts, tiles, hidden)
    rom.save_and_close()

