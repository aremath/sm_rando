from sm_rando.world_rando.fixed_cmaps import *
from sm_rando.world_rando.concrete_map import *
from sm_rando.world_rando.map_viz import *

if __name__ == "__main__":
    dimensions = MCoords(64,32)
    gt_map = mk_area(MCoords(10,10), dimensions, golden_torizo_boss_area)
    croc_map = mk_area(MCoords(20,20), dimensions, crocomire_boss_area)
    eu_map = mk_area(MCoords(44,10), dimensions, elevator_up_area)
    ed_map = mk_area(MCoords(30,20), dimensions, elevator_down_area)
    example_map = gt_map.compose(croc_map)
    example_map = example_map.compose(eu_map)
    example_map = example_map.compose(ed_map)
    map_viz(example_map, "map.png", "encoding/map_tiles")
