
items = ["B", "PB", "SPB", "S", "M", "G", "SA", "V", "GS", "SB", "HJ", "MB", "CB", "WB", "E", "PLB", "IB", "SJ", "Spazer", "RT", "XR"]
bosses = ["Kraid", "Phantoon", "Draygon", "Ridley", "Mother_Brain"]
minibosses = ["Botwoon", "Spore_Spawn", "Golden_Torizo", "Bomb_Torizo", "Crocomire"]

all_things = items + bosses + minibosses

item_types = items[:]
item_types.remove("B")
item_types = item_types + ["Bombs"]
boss_types = bosses + minibosses + ["Ceres_Ridley"]
special_types = ["Drain", "Shaktool", "START", "Statues"]

door_types = ["L", "R", "B", "T", "ET", "EB", "TS", "BS", "LMB", "RMB"]

regions = {
    "Wrecked_Ship" : ["Phantoon"],
    "Maridia"      : ["Draygon", "Botwoon"],
    "Crateria"     : ["Bomb_Torizo", "START"], # technically start could be in Ceres or anywhere I guess
    "Norfair"      : ["Golden_Torizo", "Ridley", "Crocomire"],
    "Brinstar"     : ["Kraid", "Spore_Spawn"],
    "Tourian"      : ["Mother_Brain"]
}
