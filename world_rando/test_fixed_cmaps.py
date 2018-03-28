from fixed_cmaps import *
from concrete_map import *
import map_viz

if __name__ == "__main__":
    gt_map = golden_torizo_boss_area()
    croc_map = map_offset(crocomire_boss_area(), MCoords(10, 10))
    example_map = add_cmaps(gt_map, croc_map, "e")
    map_viz.map_viz(example_map, "map.png", "../encoding/map_tiles")
