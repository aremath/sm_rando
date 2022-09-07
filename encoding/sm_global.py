items = ["B", "PB", "SPB", "S", "M", "G", "SA", "V", "GS", "SB", "HJ", "MB", "CB", "WB", "E", "PLB", "IB", "SJ", "Spazer", "RT", "XR"]
# Translate item codes to real item names
item_translate = {
        "START": "START",
        "B": "Bombs",
        "PB": "Power_Bombs",
        "SPB": "Spring_Ball",
        "S" : "Super_Missiles",
        "M" : "Missiles",
        "SA": "Screw_Attack",
        "G" : "Grapple_Beam",
        "V" : "Varia_Suit",
        "GS" : "Gravity_Suit",
        "SB" : "Speed_Booster",
        "HJ" : "Hi_Jump",
        "MB" : "Morph",
        "CB" : "Charge_Beam",
        "WB" : "Wave_Beam",
        "E" : "Energy_Tank",
        "PLB" : "Plasma_Beam",
        "IB" : "Ice_Beam",
        "SJ" : "Space_Jump",
        "RT" : "Reserve_Tank",
        "XR" : "XRay",
        "Spazer": "Spazer",
        "Kraid" : "Kraid",
        "Draygon": "Draygon",
        "Ridley" : "Ridley",
        "Phantoon": "Phantoon",
        "Mother_Brain": "Mother_Brain",
        "Spore_Spawn": "Spore_Spawn",
        "Botwoon" : "Botwoon",
        "Crocomire" : "Crocomire",
        "Bomb_Torizo": "Bomb_Torizo",
        "Golden_Torizo": "Golden_Torizo",
        "Drain": "Drain",
        "Shaktool": "Shaktool",
        "Statues": "Statues",
        }
bosses = ["Kraid", "Phantoon", "Draygon", "Ridley", "Mother_Brain"]
minibosses = ["Botwoon", "Spore_Spawn", "Golden_Torizo", "Bomb_Torizo", "Crocomire"]

all_things = items + bosses + minibosses

item_types = items[:]
item_types.remove("B")
item_types = item_types + ["Bombs"]
boss_types = bosses + minibosses + ["Ceres_Ridley"]
special_types = ["Drain", "Shaktool", "START", "Statues"]

door_types = ["L", "R", "B", "T", "ET", "EB", "TS", "BS", "LMB", "RMB"]
# Translate door codes to actual names
door_translate = {
        "T": "Top",
        "B": "Bottom",
        "L": "Left",
        "R": "Right",
        "ET": "Elevator_Top",
        "EB": "Elevator_Bottom",
        "RMB": "Right_Morph_Ball",
        "LMB": "Left_Morph_Ball",
        "TS": "Top_Sand",
        "BS": "Bottom_Sand",
        }

door_hookups = {
    "L": "R",
    "R": "L",
    "T": "B",
    "B": "T",
    "ET": "EB",
    "EB": "ET",
    "TS": "BS",
    "BS": "TS",
    "LMB": "RMB",
    "RMB": "LMB"
}


regions = {
    "Wrecked_Ship": ["Phantoon"],
    "Maridia": ["Draygon", "Botwoon"],
    "Crateria": ["Bomb_Torizo", "START"], # technically start could be in Ceres or anywhere I guess
    "Norfair": ["Golden_Torizo", "Ridley", "Crocomire"],
    "Brinstar": ["Kraid", "Spore_Spawn"],
    "Tourian": ["Mother_Brain"],
}
