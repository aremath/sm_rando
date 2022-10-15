# Default generation settings for the world generator.
import random
from bidict import bidict
from world_rando import concrete_map
from world_rando.coord import Coord
from encoding import sm_global

def rand_m(p1, p2):
    return concrete_map.manhattan(p1, p2) + random.uniform(0,6)

def less_rand_d(p1, p2):
    return concrete_map.euclidean(p1, p2) + random.uniform(0,6)

def rand_d(p1, p2):
    return concrete_map.euclidean(p1, p2) + random.uniform(0,9)

region_weights = {"Wrecked_Ship" : 2,
                    "Maridia"   : 4,
                    "Crateria"  : 4,
                    "Norfair"   : 4,
                    "Brinstar"  : 4,
                    "Tourian"   : 1,} # Abstract_Map, Item_Order_Graph

region_map = bidict({
                    0: "Crateria",
                    1: "Brinstar",
                    2: "Norfair",
                    3: "Wrecked_Ship",
                    4: "Maridia",
                    5: "Tourian",
                    6: "Ceres",
                    7: "Debug",
                })

class Region(object):
    
    def __init__(self, name, region_id=None, size=Coord(54,30), required_nodes=None, partition_weight=None):
        self.name = name
        if region_id is None:
            self.region_id = region_map.inv[name]
        else:
            self.region_id = region_id
        self.size = size
        # Which nodes are required to be in which regions
        # Key: Region name
        # Value: [node]
        if required_nodes is None:
            self.required_nodes = sm_global.regions[name]
        else:
            self.requred_nodes = required_nodes
        # How aggressively each region grabs nodes (approximately related to eventual region size)
        # Larger values allow more nuance, but are also higher variance
        if partition_weight is None:
            self.partition_weight = region_weights[name]
        else:
            self.partition_weight = partition_weight

    def __repr__(self):
        return f"Region({self.name})"

    # Need this for consistent elevator names
    def __lt__(self, other):
        return self.name < other.name

    #TODO: ensure no equality checking across different definitions of the same region?
    # This is good for convenience
    def __eq__(self, other):
        return self.name == other.name

    # Hash by name for convenience
    def __hash__(self):
        return hash(self.name)

default_regions = [Region(name) for name in sm_global.regions.keys()]

global_settings_d = {
    # Which regions to generate - A region that does not appear in this table will not be generated.
    "regions"   :   default_regions
    }

abstract_map_settings_d = {
    # Function returning the list of required item nodes that will be added to the graph
    # Each node is treated as a required item, and a plan will be formed for obtaining it
    # These are functions because a more sophisticated system might generate these rather than having them be fixed.
    #TODO: What to do about nodes like "Drain"?
    "required_nodes"    :   list(sm_global.all_things),
    # Constraint file to use for determining global item order
    # Parsed by encoding/item_order.py
    "node_ordering"     :   "encoding/dsl/item_order.txt",
    # Function returning how many extra items of each type to add
    "extra_nodes"       :   {"S": 10, "PB": 10, "M": 15, "E": 12, "Save": 10}, # Abstract_Map, Item_Order_Graph
    # Constraint file to use for determining global region order
    "region_ordering"   :   "encoding/dsl/region_order.txt",
    }

concrete_map_settings_d = {
    # The distance metric to use when finding random paths
    "distance_metric"   :   rand_d, # map_gen, less_naive
    # The desired average room size, in map tiles.
    "room_size"         :   5, # map_gen.map_gen
    # Spring model constants
    #TODO: validate this
    "n_iterations"      :   50,
    "spring_constant"   :   2,
    "equilibrium"       :   3,
    "spring_dt"         :   0.1, # map_gen.node_place
    "spring_damping"    :   0.9,
    # Region-specific map size restrictions
    # At most 64,32, but leave some space for elevators
    "region_sizes"      :   {"Wrecked_Ship" : Coord(54, 30),
                                "Maridia"   : Coord(54, 30),
                                "Crateria"  : Coord(54, 30),
                                "Norfair"   : Coord(54, 30),
                                "Brinstar"  : Coord(54, 30),
                                "Tourian"   : Coord(54, 30),
                            },
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
    "max_room_entrance_size"    :   7,
    "patterns"                  :   "encoding/patterns",
    }

default_setting_list = [global_settings_d, abstract_map_settings_d, concrete_map_settings_d, room_gen_settings_d]

def global_check(g_set):
    regs = g_set["regions"]
    # Ensure no two regions have the same name
    assert len(set(regs)) == len(regs)

def concrete_check(c_set):
    for region, size in c_set["region_sizes"].items():
        assert (size.x <= 64  and size.y <= 32), f"{region} has invalid size: {size}"

# Need to register the check/fix functions here
check_fns = [global_check, None, concrete_check, None]

class WorldGenSettings(object):

    def __init__(self, global_settings= None, abstract_map_settings=None, concrete_map_settings=None, room_gen_settings=None):
        # If a single setting is unspecified, use defaults
        new_setting_list = [global_settings, abstract_map_settings, concrete_map_settings, room_gen_settings]
        for i in range(len(new_setting_list)):
            if new_setting_list[i] is None:
                new_setting_list[i] = {}
        sets = []
        for f, d, n in zip(check_fns, default_setting_list, new_setting_list):
            news = d.copy()
            news.update(n)
            # Apply the 'fix fn'
            if f is not None:
                f(news)
            sets.append(news)
        gs, amaps, cmaps, rgens = sets
        self.global_settings = gs
        self.abstract_map_settings = amaps
        self.concrete_map_settings = cmaps
        self.room_gen_settings =  rgens

default_settings = WorldGenSettings()

# Settings for a "small" map generation that includes the base game up through Kraid
global_settings_s = {
    "regions"   : [Region("Crateria"), Region("Brinstar")]
}

amap_settings_s = {
        "required_nodes"    : ["MB", "M", "Bomb_Torizo", "B", "CB", "Spore_Spawn", "S", "Spazer", "HJ", "Kraid"],
        "node_ordering"     : "encoding/dsl/item_order_small.txt",
        "extra_nodes"       : {"M": 4, "S": 2, "Save": 3},
        }

cmap_settings_s = {
        }

room_settings_s = {
        }

small_settings = WorldGenSettings(global_settings_s, amap_settings_s, cmap_settings_s, room_settings_s)

# Tiny scenario
global_settings_t = {
    "regions"   : [Region("Crateria", size=Coord(23,23))]
}
amap_settings_t = {
        "required_nodes"    : ["MB", "M", "B"],
        "node_ordering"     : "encoding/dsl/item_order_small.txt",
        "extra_nodes"       : {"M": 1, "Save": 1},
        }

cmap_settings_t = {
        "equilibrium"       : 1,
        "room_size"         : 3,
        }

room_settings_t = {
        }

tiny_settings = WorldGenSettings(global_settings_t, amap_settings_t, cmap_settings_t, room_settings_t)
