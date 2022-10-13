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
    # Function returning the list of required item nodes that will be added to the graph
    # Each node is treated as a required item, and a plan will be formed for obtaining it
    # These are functions because a more sophisticated system might generate these rather than having them be fixed.
    #TODO: What to do about nodes like "Drain"?
    "required_nodes_f"    :   lambda: list(sm_global.all_things),
    # Constraint file to use for determining global item order
    # Parsed by encoding/item_order.py
    "node_ordering"     :   "encoding/dsl/item_order.txt",
    # Function returning how many extra items of each type to add
    "extra_nodes_f"       :   lambda: {"S": 10, "PB": 10, "M": 15, "E": 12, "Save": 10}, # Abstract_Map, Item_Order_Graph
    # Which regions to generate - A region that does not appear in this table will not be generated.
    "regions"           :   list(sm_global.regions.keys()),
    # Constraint file to use for determining global region order
    "region_ordering"   :   "encoding/dsl/region_order.txt",
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

default_setting_list = [abstract_map_settings_d, concrete_map_settings_d, room_gen_settings_d]

def abstract_fix(ab_set):
    ab_set["region_nodes"] = {k: v for k,v in ab_set["region_nodes"].items() if k in ab_set["regions"]}
    ab_set["region_weights"] = {k: v for k,v in ab_set["region_weights"].items() if k in ab_set["regions"]}
    # Ensure that every region has a definition, and every definition has a region
    assert len(ab_set["region_nodes"]) == len(ab_set["regions"])
    assert len(ab_set["region_weights"]) == len(ab_set["regions"])
    # Call the "node generation" / "extra node generation" functions to get the concrete values.
    # Since these might depend on RNG, we only want to call them exactly once, here.
    #TODO: is this reasoning right? If not, when to call them?
    # May want to be able to instantiate a settings without generating the relevant data
    # then the data is generated just in time on first access?
    # For now this is ok.
    ab_set["required_nodes"] = ab_set["required_nodes_f"]()
    ab_set["extra_nodes"] = ab_set["extra_nodes_f"]()

ident = lambda x: x

fix_fns = [abstract_fix, ident, ident]

class WorldGenSettings(object):

    def __init__(self, abstract_map_settings=None, concrete_map_settings=None, room_gen_settings=None):
        # If a single setting is unspecified, use defaults
        new_setting_list = [abstract_map_settings, concrete_map_settings, room_gen_settings]
        for i in range(len(new_setting_list)):
            if new_setting_list[i] is None:
                new_setting_list[i] = {}
        sets = []
        for f, d, n in zip(fix_fns, default_setting_list, new_setting_list):
            news = d.copy()
            news.update(n)
            # Apply the 'fix fn'
            f(news)
            sets.append(news)
        amaps, cmaps, rgens = sets
        self.abstract_map_settings = amaps
        self.concrete_map_settings = cmaps
        self.room_gen_settings =  rgens

default_settings = WorldGenSettings()

# Settings for a "small" map generation that includes the base game up through Kraid
#TODO: Spore_Spawn
amap_settings_s = {
        "required_nodes_f"    : lambda: ["MB", "M", "Bomb_Torizo", "B", "CB", "S", "Spazer", "HJ", "Kraid"],
        "node_ordering"     : "encoding/dsl/item_order_small.txt",
        "extra_nodes_f"       : lambda: {"M": 4, "S": 2, "Save": 3},
        "regions"           : ["Crateria", "Brinstar"],
        "region_nodes"      : {"Crateria": ["Bomb_Torizo", "START"],
                                "Brinstar": ["Kraid"]},
        }

cmap_settings_s = {
        }

room_settings_s = {
        }

small_settings = WorldGenSettings(amap_settings_s, cmap_settings_s, room_settings_s)
