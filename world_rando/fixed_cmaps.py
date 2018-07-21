from concrete_map import *

#TODO: how to make sure we generate the draygon item room?
#TODO: this is outdated!

def kraid_boss_area():
    """Returns the Kraid Boss Area cmap."""
    cmap = {}
    cmap[MCoords(1,0)] = MapTile("")
    cmap[MCoords(1,0)].is_fixed = True
    cmap[MCoords(1,-1)] = MapTile("")
    cmap[MCoords(1,-1)].is_fixed = True
    cmap[MCoords(2,0)] = MapTile("")
    cmap[MCoords(2,0)].is_fixed = True
    cmap[MCoords(2,-1)] = MapTile("")
    cmap[MCoords(2,-1)].is_fixed = True
    cmap[MCoords(3,0)] = MapTile("")
    cmap[MCoords(3,0)].is_fixed = True
    cmap[MCoords(3,0)].is_item = True
    cmap[MCoords(3,0)].walls = set(["L"])
    cmap[MCoords(2,0)].walls = set(["R"])
    cmap[MCoords(1,0)].walls  = set(["L"])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls  = set(["R"])
    return cmap

def phantoon_boss_area():
    """Returns the Phantoon Boss Area cmap."""
    cmap = {}
    cmap[MCoords(1,0)] = MapTile("")
    cmap[MCoords(1,0)].is_fixed = True
    cmap[MCoords(1,0)].is_item = True
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls  = set(["R"])
    return cmap

def draygon_boss_area():
    """Returns the Draygon Boss Area cmap."""
    cmap = {}
    cmap[MCoords(-1,0)] = MapTile("")
    cmap[MCoords(-1,0)].is_fixed = True
    cmap[MCoords(-1,1)] = MapTile("")
    cmap[MCoords(-1,1)].is_fixed = True
    cmap[MCoords(-2,0)] = MapTile("")
    cmap[MCoords(-2,0)].is_fixed = True
    cmap[MCoords(-2,1)] = MapTile("")
    cmap[MCoords(-2,1)].is_fixed = True
    cmap[MCoords(-3,1)] = MapTile("")
    cmap[MCoords(-3,1)].is_fixed = True
    cmap[MCoords(-3,1)].is_item = True
    cmap[MCoords(-3,1)].walls = set(["R"])
    cmap[MCoords(-2,1)].walls = set(["L"])
    cmap[MCoords(-1,0)].walls  = set(["R"])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls  = set(["L"])
    return cmap

def ridley_boss_area():
    """Returns the Ridley Boss Area cmap."""
    cmap = {}
    cmap[MCoords(-1,0)] = MapTile("")
    cmap[MCoords(-1,0)].is_fixed = True
    cmap[MCoords(-1,1)] = MapTile("")
    cmap[MCoords(-1,1)].is_fixed = True
    cmap[MCoords(-2,1)] = MapTile("")
    cmap[MCoords(-2,1)].is_fixed = True
    cmap[MCoords(-2,1)].is_item = True
    cmap[MCoords(-2,1)].walls = ["R"]
    cmap[MCoords(-1,1)].walls = ["L"]
    cmap[MCoords(-1,0)].walls  = ["R"]
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls  = ["L"]
    return cmap

#TODO: how to make sure that the other side is used?

def mother_brain_boss_area():
    """Returns the Ridley Boss Area cmap."""
    cmap = {}
    cmap[MCoords(-1,0)] = MapTile("")
    cmap[MCoords(-1,0)].is_fixed = True
    cmap[MCoords(-2,0)] = MapTile("")
    cmap[MCoords(-2,0)].is_fixed = True
    cmap[MCoords(-3,0)] = MapTile("")
    cmap[MCoords(-3,0)].is_fixed = True
    cmap[MCoords(-4,0)] = MapTile("")
    cmap[MCoords(-4,0)].is_fixed = True
    cmap[MCoords(-4,0)].is_item = True
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls  = set(["L"])
    cmap[MCoords(-5,0)] = MapTile("")
    cmap[MCoords(-5,0)].walls  = set(["R"])
    return cmap

def bomb_torizo_boss_area():
    return phantoon_boss_area()

def spore_spawn_boss_area():
    """Returns the Ridley Boss Area cmap."""
    cmap = {}
    cmap[MCoords(0,-1)] = MapTile("")
    cmap[MCoords(0,-1)].is_fixed = True
    cmap[MCoords(0,-1)].is_item = True
    cmap[MCoords(0,-2)] = MapTile("")
    cmap[MCoords(0,-2)].is_fixed = True
    cmap[MCoords(0,-3)] = MapTile("")
    cmap[MCoords(0,-3)].is_fixed = True
    cmap[MCoords(1,-3)] = MapTile("")
    cmap[MCoords(1,-3)].is_fixed = True
    cmap[MCoords(1,-3)].is_item = True
    cmap[MCoords(0,-1)].walls = set(["U"])
    cmap[MCoords(0,-3)].walls = set(["R"])
    cmap[MCoords(1,-3)].walls = set(["L"])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls = set(["U"])
    return cmap

def crocomire_boss_area():
    """Returns the Ridley Boss Area cmap."""
    cmap = {}
    for i in range(9):
        cmap[MCoords(-4+i, 1)] = MapTile("")
        cmap[MCoords(-4+i, 1)].is_fixed = True

    cmap[MCoords(-4,1)].is_item = True
    cmap[MCoords(2,1)].is_item = True
    cmap[MCoords(4,1)].is_item = True
    cmap[MCoords(-4,1)].walls = set(["R"])
    cmap[MCoords(-3,1)].walls = set(["L"])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls = set(["D"])
    return cmap

def botwoon_boss_area():
    """Returns the Ridley Boss Area cmap."""
    cmap = {}
    cmap[MCoords(1,0)] = MapTile("")
    cmap[MCoords(1,0)].is_fixed = True
    cmap[MCoords(1,0)].is_item = True
    cmap[MCoords(2,0)] = MapTile("")
    cmap[MCoords(2,0)].is_fixed = True
    cmap[MCoords(3,0)] = MapTile("")
    cmap[MCoords(3,0)].is_fixed = True
    cmap[MCoords(3,0)].is_item = True
    cmap[MCoords(1,0)].walls = set(["L","R"])
    cmap[MCoords(2,0)].walls = set(["L","R"])
    cmap[MCoords(3,0)].walls = set(["L"])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls = set(["R"])
    return cmap

def golden_torizo_boss_area():
    """Returns the Golden Torizo Boss Area cmap."""
    cmap = {}
    cmap[MCoords(1,0)] = MapTile("")
    cmap[MCoords(1,0)].is_fixed = True
    cmap[MCoords(1,0)].is_item = True
    cmap[MCoords(2,0)] = MapTile("")
    cmap[MCoords(2,0)].is_fixed = True
    cmap[MCoords(2,0)].is_item = True
    cmap[MCoords(1,1)] = MapTile("")
    cmap[MCoords(1,1)].is_fixed = True
    cmap[MCoords(2,1)] = MapTile("")
    cmap[MCoords(2,1)].is_fixed = True
    cmap[MCoords(3,1)] = MapTile("")
    cmap[MCoords(3,1)].is_fixed = True
    cmap[MCoords(3,1)].is_item = True
    cmap[MCoords(1,0)].walls = set(["R","D"])
    cmap[MCoords(2,1)].walls = set(["R"])
    cmap[MCoords(3,1)].walls = set(["L"])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls = set(["R"])
    return cmap

def elevator_down():
    """Returns the cmap for a down elevator."""
    cmap = {}
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,1)] = MapTile("")
    cmap[MCoords(0,1)].is_fixed = True
    cmap[MCoords(0,1)].is_e_tile = True
    return cmap

def elevator_up():
    """Returns the cmap for an up elevator."""
    cmap = {}
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,-1)] = MapTile("")
    cmap[MCoords(0,-1)].is_fixed = True
    cmap[MCoords(0,-1)].is_e_tile = True
    return cmap
