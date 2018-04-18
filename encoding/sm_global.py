
items = ["B", "PB", "SPB", "S", "M", "G", "SA", "V", "GS", "SB", "HJ", "MB", "CB", "WB", "E", "PLB", "IB", "SJ", "Spazer", "RT", "XR"]
bosses = ["Kraid", "Phantoon", "Draygon", "Ridley", "Mother_Brain"]
minibosses = ["Botwoon", "Spore_Spawn", "Golden_Torizo", "Bomb_Torizo", "Crocomire"]

all_things = items + bosses + minibosses

item_types = items[:]
item_types.remove("B")
item_types = item_types + ["Bombs"]
boss_types = bosses + minibosses + ["Ceres_Ridley"]
special_types = ["Drain", "Shaktool", "START"]

door_types = ["L", "R", "B", "T", "ET", "EB", "TS", "BS", "LMB", "RMB"]

regions = {
    "Wrecked_Ship" : ["Phantoon"],
    "Maridia"      : ["Draygon", "Botwoon"],
    "Crateria"     : ["Bomb_Torizo", "START"], # technically start could be in Ceres or anywhere I guess
    "Norfair"      : ["Golden_Torizo", "Ridley", "Crocomire"],
    "Brinstar"     : ["Kraid", "Spore_Spawn"],
    "Tourian"      : ["Mother_Brain"]
}

region_map_locs = { # hidden |  tiles
    "Wrecked_Ship" : (0x11a27, 0x1ab000),
    "Maridia"      : (0x11b27, 0x1ac000),
    "Crateria"     : (0x11727, 0x1a9000),
    "Norfair"      : (0x11927, 0x1aa000),
    "Brinstar"     : (0x11827, 0x1a8000),
    "Tourian"      : (0x11c27, 0x1ad000)
}

