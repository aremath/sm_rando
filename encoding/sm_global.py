
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

