#TODO: version control of sm_junk
#TODO: caching
import time
import json
import os
import numpy as np
from bdds.node_bdds import MapsInfo
from rom_tools.rom_manager import RomManager
from abstraction_validation.abstractify import abstractify_pos_global
from abstraction_validation.sm_paths import all_global_positions
from world_rando.coord import Coord

f = os.path.dirname(__file__)
rom = RomManager(f + "/../roms/sm_clean.sfc", f + "/../roms/sm_junk.smc")
map_info = MapsInfo(f + "/encoding/dsl/rooms_for_alloy.txt", \
                   f + "/encoding/dsl/exits_for_alloy.txt",
                   f + "/output/ram_snes9x.bin",
                   rom)
policy_id = map_info.context.bdd.load(f + "/output/node_policy_det.dddmp")[0]
# The map on the website from bin0al uses a slightly different coordinate system
# These are the offsets for bin0al's map
map_area_offsets = {
0: Coord(3, 10),
1: Coord(0, 28),
2: Coord(31, 48),
3: Coord(37, 0),
4: Coord(28, 28),
5: Coord(0, 10),
#Out of bounds
6: Coord(0, -10),
7: Coord(0, 0),
}

all_posns2 = all_global_positions(map_info.rooms, map_info.parsed_rom, map_area_offsets);

def filter_posns(l):
    return [all_posns2[p] for p in l if p in all_posns2]

#TODO: inference times
def mk_advice(ram_data, goal_node):
    state = map_info.estimate_state_from_ram(ram_data)
    map_info.goal_node = goal_node
    # Player pos
    pos = abstractify_pos_global(ram_data, map_area_offsets)
    output = {
        "player_pos": None,
        "map_lines": None,
        "emu_lines": None
    }
    output["player_pos"] = {"X": int(pos.x), "Y": int(pos.y)}
    # Client is responsible for remembering past info
    if state is None:
        return output
    # Abstract lines with only node info
    lines_abs = map_info.generate_lines(state, policy_id)
    # Lines with positional info
    lines_concrete = {x: filter_posns(lines_abs[x]) for x in lines_abs.keys()}
    #lines_concrete = {"next_step": filter_posns(lines_abs["next_step"]),
    #    "next_item": filter_posns(lines_abs["next_item"]),
    #    "remaining_path": filter_posns(lines_abs["remaining_path"])}
    # Emulator Line info
    next_node = map_info.get_step_advice(state, policy_id)
    next_node_pos = map_info.all_posns[next_node]
    emu_lines = {"X": next_node_pos.x, "Y": next_node_pos.y, "Node_Inference": None, "Path_Inference": None}
    output["map_lines"] = lines_concrete
    output["emu_lines"] = emu_lines
    return output

if __name__ == "__main__":
    ram_data = np.fromfile(map_info.bin_path, dtype="int16")
    advice = mk_advice(ram_data, "END")
    print(json.dumps(advice))

