from concrete_map import *

#TODO: how to make sure we generate the draygon item room?

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
    cmap[MCoords(3,0)].walls = set([MCoords(2,0)])
    cmap[MCoords(2,0)].walls = set([MCoords(3,0)])
    cmap[MCoords(1,0)].walls  = set([MCoords(0,0)])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls  = set([MCoords(1,0)])
    return cmap

def phantoon_boss_area():
    """Returns the Kraid Boss Area cmap."""
    cmap = {}
    cmap[MCoords(1,0)] = MapTile("")
    cmap[MCoords(1,0)].is_fixed = True
    cmap[MCoords(1,0)].is_item = True
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls  = set([MCoords(1,0)])
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
    cmap[MCoords(-3,1)].walls = set([MCoords(-2,1)])
    cmap[MCoords(-2,1)].walls = set([MCoords(-3,1)])
    cmap[MCoords(-1,0)].walls  = set([MCoords(0,0)])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls  = set([MCoords(-1,0)])
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
    cmap[MCoords(-2,1)].walls = [MCoords(-1,1)]
    cmap[MCoords(-1,1)].walls = [MCoords(-2,1)]
    cmap[MCoords(-1,0)].walls  = [MCoords(0,0)]
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls  = [MCoords(-1,0)]
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
    cmap[MCoords(0,0)].walls  = set([MCoords(-1,0)])
    cmap[MCoords(-5,0)] = MapTile("")
    cmap[MCoords(-5,0)].walls  = set([MCoords(-4,0)])
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
    cmap[MCoords(0,-1)].walls = set([MCoords(0,0)])
    cmap[MCoords(0,-3)].walls = set([MCoords(1,-3)])
    cmap[MCoords(1,-3)].walls = set([MCoords(0,-3)])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls = set([MCoords(0,-1)])
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
    cmap[MCoords(-4,1)].walls = set([MCoords(-3,1)])
    cmap[MCoords(-3,1)].walls = set([MCoords(-4,1)])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls = set([MCoords(0,1)])
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
    cmap[MCoords(1,0)].walls = set([MCoords(0,0),MCoords(2,0)])
    cmap[MCoords(2,0)].walls = set([MCoords(1,0),MCoords(3,0)])
    cmap[MCoords(3,0)].walls = set([MCoords(2,0)])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls = set([MCoords(1,0)])
    return cmap

def golden_torizo_boss_area():
    """Returns the Ridley Boss Area cmap."""
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
    cmap[MCoords(1,0)].walls = set([MCoords(2,0),MCoords(1,1)])
    cmap[MCoords(2,1)].walls = set([MCoords(3,1)])
    cmap[MCoords(3,1)].walls = set([MCoords(2,1)])
    elide_walls(cmap)
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,0)].walls = set([MCoords(1,0)])
    return cmap

def elevator_down():
    """Returns the cmap for an elevator."""
    cmap = {}
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,1)] = MapTile("")
    cmap[MCoords(0,1)].is_fixed = True
    cmap[MCoords(0,1)].is_e_tile = True
    return cmap

def elevator_up():
    """Returns the cmap for an elevator."""
    cmap = {}
    cmap[MCoords(0,0)] = MapTile("")
    cmap[MCoords(0,-1)] = MapTile("")
    cmap[MCoords(0,-1)].is_fixed = True
    cmap[MCoords(0,-1)].is_e_tile = True
    return cmap
