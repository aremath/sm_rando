# Default generation settings for the world generator.
import random
from world_rando import concrete_map
from encoding import sm_global

def rand_m(p1, p2):
    return concrete_map.manhattan(p1, p2) + random.uniform(0,6)

def less_rand_d(p1, p2):
    return concrete_map.euclidean(p1, p2) + random.uniform(0,6)

def rand_d(p1, p2):
    return concrete_map.euclidean(p1, p2) + random.uniform(0,9)

abstract_map_settings_d = {
    # List of required item nodes that will be added to the graph
    # Each node is treated as a required item, and a plan will be formed for obtaining it
    #TODO: What to do about nodes like "Drain"?
    "required_nodes"    :   list(sm_global.all_things),
    # How many extra items of each type to add
    "extra_nodes"       :   {"S": 10, "PB": 10, "M": 15, "E": 12, "Save": 10}, # Abstract_Map, Item_Order_Graph
    # Which nodes are required to be in which regions
    # Key: Region name
    # Value: [node]
    "region_nodes"      :   sm_global.regions,
    # How aggressively each region grabs nodes (approximately related to eventual region size)
    # Larger values allow more nuance, but are also higher variance
    "region_weights"    :   {"Wrecked_Ship" : 2,
                                "Maridia"   : 4,
                                "Crateria"  : 4,
                                "Norfair"   : 4,
                                "Brinstar"  : 4,
                                "Tourian"   : 1,} # Abstract_Map, Item_Order_Graph
        }

concrete_map_settings_d = {
    # The distance metric to use when finding random paths
    "distance_metric"   :   rand_d, # map_gen, less_naive
    # The desired average room size, in map tiles.
    "room_size"         :   5, # map_gen.map_gen
    # Spring model constants
    "n_iterations"      :   50,
    "spring_constant"   :   2,
    "equilibrium"       :   3,
    "spring_dt"         :   0.1, # map_gen.node_place
    "spring_damping"    :   0.9,
    }

room_gen_settings_d = {
    # How often each item is given each type of item location
    # Order is [chozo_statue, pedestal, hidden]
    # Default is for missing items
    #TODO: fill out this table
    "item_placement_chances"    :   { "default" : [50, 50, 0]
        },
    # Max number of partitions in a single room
    "max_room_partitions"       :   20,
    # Minimum size of any partition (in both x and y)
    "min_room_partition_size"   :   3,
    # TODO: entrances to morph subrooms can be as small as 1...
    # Min and max size for the entrance to a subroom
    "min_room_entrance_size"    :   3,
    "max_room_entrance_size"    :   7
    }

class WorldGenSettings(object):

    def __init__(self, abstract_map_settings, concrete_map_settings, room_gen_settings):
        self.abstract_map_settings = abstract_map_settings
        self.concrete_map_settings = concrete_map_settings
        self.room_gen_settings =  room_gen_settings

default_settings = WorldGenSettings(abstract_map_settings_d, concrete_map_settings_d, room_gen_settings_d)
