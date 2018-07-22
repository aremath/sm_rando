from concrete_map import *

#TODO: how to make sure we generate the draygon item room?
#TODO: this is outdated!
#TODO: these functions should return a cmap, a list of implicit doors, and a list of implicit rooms.

default_extent = MCoords(60,30)

def kraid_boss_area(pos):
    """Returns the Kraid Boss Area cmap."""
    cmap = ConcreteMap()
    cmap[pos + MCoords(1,0)] = MapTile(_fixed=True,_walls=set(["L"]))
    cmap[pos + MCoords(1,-1)] = MapTile(_fixed=True)
    cmap[pos + MCoords(2,0)] = MapTile(_fixed=True,_walls=set(["R"]))
    cmap[pos + MCoords(2,-1)] = MapTile(_fixed=True)
    cmap[pos + MCoords(3,0)] = MapTile(_fixed=True,_item=True,_walls=set(["L"]))
    elide_walls(cmap)
    cmap[pos] = MapTile(_walls=set(["R"]))
    return cmap

def phantoon_boss_area(pos):
    """Returns the Phantoon Boss Area cmap."""
    cmap = ConcreteMap()
    cmap[pos + MCoords(1,0)] = MapTile(_fixed=True,_item=True)
    elide_walls(cmap)
    cmap[pos] = MapTile(_walls=set(["R"]))
    return cmap

def draygon_boss_area(pos):
    """Returns the Draygon Boss Area cmap."""
    cmap = ConcreteMap()
    cmap[pos + MCoords(-1,0)] = MapTile(_fixed=True,_walls=set(["R"]))
    cmap[pos + MCoords(-1,1)] = MapTile(_fixed=True)
    cmap[pos + MCoords(-2,0)] = MapTile(_fixed=True)
    cmap[pos + MCoords(-2,1)] = MapTile(_fixed=True,_walls=set(["L"]))
    cmap[pos + MCoords(-3,1)] = MapTile(_fixed=True,_item=True,_walls=set(["R"]))
    elide_walls(cmap)
    cmap[pos] = MapTile(_walls=set(["L"]))
    return cmap

def ridley_boss_area(pos):
    """Returns the Ridley Boss Area cmap."""
    cmap = ConcreteMap()
    cmap[pos + MCoords(-1,0)] = MapTile(_fixed=True,_walls=set(["R"]))
    cmap[pos + MCoords(-1,1)] = MapTile(_fixed=True,_walls=set(["L"]))
    cmap[pos + MCoords(-2,1)] = MapTile(_fixed=True,_item=True,_walls=set(["R"]))
    elide_walls(cmap)
    cmap[pos] = MapTile(_walls=set(["L"]))
    return cmap

#TODO: how to make sure that the other side is used?
def mother_brain_boss_area(pos):
    """Returns the Mother Brain Boss Area cmap."""
    cmap = ConcreteMap()
    cmap[pos + MCoords(-1,0)] = MapTile(_fixed=True)
    cmap[pos + MCoords(-2,0)] = MapTile(_fixed=True)
    cmap[pos + MCoords(-3,0)] = MapTile(_fixed=True)
    cmap[pos + MCoords(-4,0)] = MapTile(_fixed=True,_item=True)
    elide_walls(cmap)
    cmap[pos] = MapTile(_walls=set(["L"]))
    cmap[pos + MCoords(-5,0)] = MapTile(_walls=set(["R"]))
    return cmap

# They're the same... for now #TODO
def bomb_torizo_boss_area(pos):
    return phantoon_boss_area(pos)

def spore_spawn_boss_area(pos):
    """Returns the Spore Spawn Boss Area cmap."""
    cmap = ConcreteMap()
    cmap[pos + MCoords(0,-1)] = MapTile(_fixed=True,_item=True,_walls=set(["U"]))
    cmap[pos + MCoords(0,-2)] = MapTile(_fixed=True)
    cmap[pos + MCoords(0,-3)] = MapTile(_fixed=True,_walls=set(["R"]))
    cmap[pos + MCoords(1,-3)] = MapTile(_fixed=True,_item=True,_walls=set(["L"]))
    elide_walls(cmap)
    cmap[pos] = MapTile(_walls=set(["U"]))
    return cmap

def crocomire_boss_area():
    """Returns the Crocomire Boss Area cmap."""
    cmap = ConcreteMap()
    for i in range(9):
        cmap[pos + MCoords(-4+i, 1)] = MapTile(_fixed=True)

    cmap[pos + MCoords(-4,1)].is_item = True
    cmap[pos + MCoords(2,1)].is_item = True
    cmap[pos + MCoords(4,1)].is_item = True
    cmap[pos + MCoords(-4,1)].walls = set(["R"])
    cmap[pos + MCoords(-3,1)].walls = set(["L"])
    elide_walls(cmap)
    cmap[pos] = MapTile(_walls=set(["D"]))
    return cmap

def botwoon_boss_area():
    """Returns the Botwoon Boss Area cmap."""
    cmap = ConcreteMap()
    cmap[pos + MCoords(1,0)] = MapTile(_fixed=True,_item=True,_walls=set(["L","R"]))
    cmap[pos + MCoords(2,0)] = MapTile(_fixed=True,_walls=set(["L","R"]))
    cmap[pos + MCoords(3,0)] = MapTile(_fixed=True,_item=True,_walls=set(["L"]))
    elide_walls(cmap)
    cmap[pos] = MapTile(_walls=set(["R"]))
    return cmap

def golden_torizo_boss_area(pos):
    """Returns the Golden Torizo Boss Area cmap."""
    cmap = ConcreteMap()
    cmap[pos + MCoords(1,0)] = MapTile(_fixed=True,_item=True,_walls=set(["R","D"]))
    cmap[pos + MCoords(2,0)] = MapTile(_fixed=True,_item=True)
    cmap[pos + MCoords(1,1)] = MapTile(_fixed=True)
    cmap[pos + MCoords(2,1)] = MapTile(_fixed=True,_walls=set(["R"]))
    cmap[pos + MCoords(3,1)] = MapTile(_fixed=True,_item=True,_walls=set(["L"]))
    elide_walls(cmap)
    cmap[pos] = MapTile(_walls=set(["R"]))
    return cmap

#TODO: arrows and shaft, and walls?

def elevator_down(pos):
    """Returns the cmap for a down elevator."""
    cmap = ConcreteMap()
    cmap[pos] = MapTile()
    cmap[pos + MCoords(0,1)] = MapTile(TileType.elevator_main_down, True)
    cmap[pos + MCoords(0,2)] = MapTile(TileType.elevator_shaft, True)
    cmap[pos + MCoords(0,3)] = MapTile(TileType.up_arrow, True)
    return cmap

def elevator_up(pos):
    """Returns the cmap for an up elevator."""
    cmap = ConcreteMap()
    cmap[pos] = MapTile()
    cmap[pos + MCoords(0,-1)] = MapTile(TileType.elevator_main_up, True)
    cmap[pos + MCoords(0,-2)] = MapTile(TileType.elevator_shaft, True)
    cmap[pos + MCoords(0,-3)] = MapTile(TileType.down_arrow, True)
    return cmap

