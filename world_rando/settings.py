# Default generation settings for the world generator.
from . import concrete_map
import random

def rand_m(p1, p2):
    return concrete_map.manhattan(p1, p2) + random.uniform(0,6)

def less_rand_d(p1, p2):
    return concrete_map.euclidean(p1, p2) + random.uniform(0,6)

def rand_d(p1, p2):
    return concrete_map.euclidean(p1, p2) + random.uniform(0,9)

abstract_map_settings = {
    # How many extra items of each type to add
    "extra_items"       :   {"S": 10, "PB": 10, "M": 15, "E": 12}, # Abstract_Map, Item_Order_Graph
    # How aggressively each region grabs nodes (approximately related to eventual region size)
    # Larger values allow more nuance, but are also higher variance
    "region_weights"    :   {"Wrecked_Ship" : 2,
                                "Maridia"   : 4,
                                "Crateria"  : 4,
                                "Norfair"   : 4,
                                "Brinstar"  : 4,
                                "Tourian"   : 1,} # Abstract_Map, Item_Order_Graph
        }

concrete_map_settings = {
    # The distance metric to use when finding random paths through the graph
    "distance_metric"   :   rand_d, # map_gen, less_naive
    # The desired average room size, in map tiles.
    "room_size"         :   5, # map_gen, less_naive
    # Spring model constants
    "n_iterations"      :   5,
    "spring_constant"   :   2,
    "equilibrium"       :   3,
    "spring_dt"         :   0.1, # map_gen, node_place
    }

room_gen_settings = {
    # How often each item is given each type of item location
    # Order is [chozo_statue, pedestal, hidden]
    # Default is for missing items
    #TODO: fill out this table
    "item_placement_chances"    :   { "default" : [50, 50, 0]
        }
    "max_room_partitions"       :   20
    "min_room_partition_size"   :   5
    }
