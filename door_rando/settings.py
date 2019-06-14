from encoding import sm_global

items = {
    "starting": 2,
    "extra":    {"M": 22,
                "S": 12,
                "PB": 10,
                "E": 14}
    }

# Time in seconds to handle the various scenarios in escape
escape = {
    "tourian":          60,
    # Per node means every node gives you this much time regardless
    # every room will consist of two nodes in escape, so this is 30s per room
    "per_node":         15,
    "Crocomire_T":      70,
    "Spore_Spawn_B":    45,
    "Golden_Torizo_R":  45,
    "Shaktool_L":       50,
    "Bowling_Alley_L2": 50
    }

def items_to_item_list(items_d):
    items_to_place = []
    assert items_d["starting"] > 0, "Must place every item at least once!"
    items_to_place.extend(items_d["starting"] * sm_global.starting_items)
    for ty, count in items_d["extra"].items():
        items_to_place.extend(count * [ty])
    assert len(items_to_place) == 100, "Total items is not 100!"
    return items_to_place

settings = [(items, "items.set"), (escape, "escape.set")]
