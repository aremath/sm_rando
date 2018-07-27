from .concrete_map import *
from functools import reduce

#TODO: how to make sure we generate the draygon item room?
#TODO: this is outdated!
#TODO: these functions should return a cmap, a list of implicit doors, and a list of implicit rooms.
#TODO: make these functions only predicated on the tile_list - i.e. a mk_area function that
# uses only the tile_list (except for elevators)

# Put the tiles in tile_list into cmap, and check if any lie outside the bounds of the cmap.
# tile_list is a [(position, maptile)]
def bounded_put_check(cmap, tile_list):
    is_valid_list = map(lambda x: cmap.bounded_put(x[0],x[1]), tile_list)
    # If any of the calls to bounded_put failed, this will be False
    return reduce(lambda x, y: x and y, is_valid_list)

# area is (position -> dimensions -> tile_list)
def mk_area(pos, dims, area):
    cmap = ConcreteMap(dims)
    # Most of the areas throw away dims, but it's useful for elevators.
    tile_list = area(pos, dims)
    # If any of the tile lie outside the bounds, this map isn't valid
    if bounded_put_check(cmap,tile_list):
        return cmap
    else:
        return None

def kraid_boss_area(pos, dims):
    return [
        (pos + MCoords(1,0), MapTile(_fixed=True,_walls=set(["L","D"]))),
        (pos + MCoords(1,-1), MapTile(_fixed=True,_walls=set(["L","U"]))),
        (pos + MCoords(2,0), MapTile(_fixed=True,_walls=set(["R","D"]))),
        (pos + MCoords(2,-1), MapTile(_fixed=True,_walls=set(["R","U"]))),
        (pos + MCoords(3,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["R"]))),
    ]

def phantoon_boss_area(pos, dims):
    """Returns the Phantoon Boss Area cmap."""
    return [
        (pos + MCoords(1,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["R"]))),
    ]

def draygon_boss_area(pos, dims):
    return [
        (pos + MCoords(-1,0), MapTile(_fixed=True,_walls=set(["R","U"]))),
        (pos + MCoords(-1,1), MapTile(_fixed=True,_walls=set(["R","D"]))),
        (pos + MCoords(-2,0), MapTile(_fixed=True,_walls=set(["L","U"]))),
        (pos + MCoords(-2,1), MapTile(_fixed=True,_walls=set(["L","D"]))),
        (pos + MCoords(-3,1), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["L"]))),
    ]
    return cmap

def ridley_boss_area(pos, dims):
    """Returns the Ridley Boss Area cmap."""
    return [
        (pos + MCoords(-1,0), MapTile(_fixed=True,_walls=set(["L","U","R"]))),
        (pos + MCoords(-1,1), MapTile(_fixed=True,_walls=set(["L","R","D"]))),
        (pos + MCoords(-2,1), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["L"]))),
    ]

#TODO: how to make sure that the other side is used?
def mother_brain_boss_area(pos, dims):
    """Returns the Mother Brain Boss Area cmap."""
    return [
        (pos + MCoords(-1,0), MapTile(_fixed=True,_walls=set(["U","R","D"]))),
        (pos + MCoords(-2,0), MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + MCoords(-3,0), MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + MCoords(-4,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","D"]))),
        (pos + MCoords(-5,0), MapTile(_walls=set(["R"]))),
        (pos, MapTile(_walls=set(["L"]))),
    ]

def bomb_torizo_boss_area(pos, dims):
    return [
        (pos + MCoords(1,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["R"]))),
    ]

def spore_spawn_boss_area(pos, dims):
    """Returns the Spore Spawn Boss Area cmap."""
    return [
        (pos + MCoords(0,-1), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos + MCoords(0,-2), MapTile(_fixed=True,_walls=set(["L","R","D"]))),
        (pos + MCoords(0,-3), MapTile(_fixed=True,_walls=set(["L","U","R"]))),
        (pos + MCoords(1,-3), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["U"]))),
    ]

def crocomire_boss_area(pos, dims):
    """Returns the Crocomire Boss Area cmap."""
    return [
        (pos + MCoords(-4, 1),MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos + MCoords(-3, 1),MapTile(_fixed=True,_walls=set(["L","U","D"]))),
        (pos + MCoords(-2, 1),MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + MCoords(-1, 1),MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + MCoords(0, 1),MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + MCoords(1, 1),MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + MCoords(2, 1),MapTile(_fixed=True,_item=True,_walls=set(["U","D"]))),
        (pos + MCoords(3, 1),MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + MCoords(4, 1),MapTile(_fixed=True,_item=True,_walls=set(["U","R","D"]))),
        (pos, MapTile(_walls=set(["D"]))),
    ]

def botwoon_boss_area(pos, dims):
    """Returns the Botwoon Boss Area cmap."""
    return [
        (pos + MCoords(1,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos + MCoords(2,0), MapTile(_fixed=True,_walls=set(["L","U","R","D"]))),
        (pos + MCoords(3,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["R"]))),
    ]

def golden_torizo_boss_area(pos, dims):
    """Returns the Golden Torizo Boss Area cmap."""
    return [
        (pos + MCoords(1,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos + MCoords(2,0), MapTile(_fixed=True,_item=True,_walls=set(["U","R"]))),
        (pos + MCoords(1,1), MapTile(_fixed=True,_walls=set(["L","D"]))),
        (pos + MCoords(2,1), MapTile(_fixed=True,_walls=set(["R","D"]))),
        (pos + MCoords(3,1), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["R"]))),
    ]

def elevator_down_area(pos, dims):
    """Returns the cmap for a down elevator."""
    e_tiles = [
        (pos, MapTile(_walls=set(["D"]))),
        (pos + MCoords(0,1), MapTile(TileType.elevator_main_down,_fixed=True,_walls=set(["L","R","U"]))),
        (pos + MCoords(0,2), MapTile(TileType.elevator_shaft,_fixed=True,_walls=set(["L","R"]))),
        (pos + MCoords(0,3), MapTile(TileType.up_arrow,_fixed=True,_walls=set(["L","R","D"]))),
    ]
    # Blank tiles down to the bottom of dims
    # Note: range(x,y) = [] when x>=y
    #TODO: dims.y + 1? is dims inclusive?
    for i in range(pos.y + 4, dims.y):
        t = (MCoords(pos.x, i), MapTile(TileType.blank,_fixed=True))
        e_tiles.append(t)
    return e_tiles

def elevator_up_area(pos, dims):
    """Returns the cmap for an up elevator."""
    e_tiles = [
        (pos, MapTile(_walls=set(["U"]))),
        (pos + MCoords(0,-1), MapTile(TileType.elevator_main_down,_fixed=True,_walls=set(["L","R","D"]))),
        (pos + MCoords(0,-2), MapTile(TileType.elevator_shaft,_fixed=True,_walls=set(["L","R"]))),
        (pos + MCoords(0,-3), MapTile(TileType.up_arrow,_fixed=True,_walls=set(["L","R","U"]))),
    ]
    # Blank tiles up to the top of dims
    for i in range(0, pos.y - 3):
        t = (MCoords(pos.x, i), MapTile(TileType.blank,_fixed=True))
        e_tiles.append(t)
    return e_tiles

def save_point_area(pos, dims):
    return [
        (pos, MapTile(_save=True))
    ]

def item_area(pos, dims):
    return [
        (pos, MapTile(_item=True))
    ]

fixed_areas = {
    "Kraid"         :   kraid_boss_area,
    "Phantoon"      :   phantoon_boss_area,
    "Draygon"       :   draygon_boss_area,
    "Ridley"        :   ridley_boss_area,
    "Bomb_Torizo"   :   bomb_torizo_boss_area,
    "Spore_Spawn"   :   spore_spawn_boss_area,
    "Botwoon"       :   botwoon_boss_area,
    "Golden_Torizo" :   golden_torizo_boss_area,
}

# node -> (pos -> dimms -> cmap)
def node_to_area(node, up_es, down_es):
    if node in up_es:
        return elevator_up_area
    elif node in down_es:
        return elevator_down_area
    elif node == "Kraid":
        return kraid_boss_area
    elif node == "Phantoon":
        return phantoon_boss_area
    elif node == "Draygon":
        return draygon_boss_area
    elif node == "Ridley":
        return ridley_boss_area
    elif node == "Bomb_Torizo":
        return bomb_torizo_boss_area
    elif node == "Spore_Spawn":
        return spore_spawn_boss_area
    elif node == "Botwoon":
        return botwoon_boss_area
    elif node == "Golden_Torizo":
        return golden_torizo_boss_area
    #TODO - save points, reserves, etc?
    else:
        return item_area
    
