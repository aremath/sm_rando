from functools import reduce
from .coord import Coord, Rect
from .concrete_map import ConcreteMap, MapTile, TileType

from sm_rando.world_rando.coord import *
from sm_rando.world_rando.concrete_map import *

#TODO: how to make sure we generate the kraid and draygon item rooms?
#TODO: these functions should return a cmap, a list of implicit doors, and a list of implicit rooms.
#TODO: make these functions only predicated on the tile_list - i.e. a mk_area function that
# uses only the tile_list (except for elevators)

def bounded_put_check(cmap, tile_list):
    """
    Put the tiles in tile_list into cmap, and check if any lie outside the bounds of the cmap.
    tile_list is a [(position, maptile)]
    """
    is_valid_list = map(lambda x: cmap.bounded_put(x[0],x[1]), tile_list)
    # If any of the calls to bounded_put failed, this will be False
    return reduce(lambda x, y: x and y, is_valid_list)

def mk_area(pos, dims, area):
    """
    Create a cmap for an area at a given position
    area is (position -> dimensions -> tile_list)
    """
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
        (pos + Coord(1,0), MapTile(_fixed=True,_walls=set(["L","D"]))),
        (pos + Coord(1,-1), MapTile(_fixed=True,_walls=set(["L","U"]))),
        (pos + Coord(2,0), MapTile(_fixed=True,_walls=set(["R","D"]))),
        (pos + Coord(2,-1), MapTile(_fixed=True,_walls=set(["R","U"]))),
        (pos + Coord(3,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["R"]))),
    ]

def kraid_bboxes(pos, dims):
    return [
        Rect(pos + Coord(1,-1), pos + Coord(3,1)),
        Rect(pos + Coord(3,0), pos + Coord(4,1))
    ]

def phantoon_boss_area(pos, dims):
    """Returns the Phantoon Boss Area cmap."""
    return [
        (pos + Coord(1,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["R"]))),
    ]

def phantoon_bboxes(pos, dims):
    return [
        Rect(pos + Coord(1,0), pos + Coord(2,1))
    ]

def draygon_boss_area(pos, dims):
    return [
        (pos + Coord(-1,0), MapTile(_fixed=True,_walls=set(["R","U"]))),
        (pos + Coord(-1,1), MapTile(_fixed=True,_walls=set(["R","D"]))),
        (pos + Coord(-2,0), MapTile(_fixed=True,_walls=set(["L","U"]))),
        (pos + Coord(-2,1), MapTile(_fixed=True,_walls=set(["L","D"]))),
        (pos + Coord(-3,1), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["L"]))),
    ]
    return cmap

def draygon_bboxes(pos, dims):
    return [
        Rect(pos + Coord(-2,0), pos + Coord(0,2)),
        Rect(pos + Coord(-3,1), pos + Coord(-2,2))
    ]

def ridley_boss_area(pos, dims):
    """Returns the Ridley Boss Area cmap."""
    return [
        (pos + Coord(-1,0), MapTile(_fixed=True,_walls=set(["L","U","R"]))),
        (pos + Coord(-1,1), MapTile(_fixed=True,_walls=set(["L","R","D"]))),
        (pos + Coord(-2,1), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["L"]))),
    ]

def ridley_bboxes(pos, dims):
    return [
        Rect(pos + Coord(-1,0), pos + Coord(0,2)),
        Rect(pos + Coord(-2,1), pos + Coord(-1,2))
    ]

#TODO: how to make sure that the other side is used?
def mother_brain_boss_area(pos, dims):
    """Returns the Mother Brain Boss Area cmap."""
    return [
        (pos + Coord(-1,0), MapTile(_fixed=True,_walls=set(["U","R","D"]))),
        (pos + Coord(-2,0), MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + Coord(-3,0), MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + Coord(-4,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","D"]))),
        (pos + Coord(-5,0), MapTile(_walls=set(["R"]))),
        (pos, MapTile(_walls=set(["L"]))),
    ]

def mother_brain_bboxes(pos, dims):
    return [
        Rect(pos + Coord(-4,0), pos + Coord(0,1)),
    ]

def bomb_torizo_boss_area(pos, dims):
    return [
        (pos + Coord(1,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["R"]))),
    ]

def bomb_torizo_bboxes(pos, dims):
    return [
        Rect(pos + Coord(1,0), pos + Coord(2,1)),
    ]

def spore_spawn_boss_area(pos, dims):
    """Returns the Spore Spawn Boss Area cmap."""
    return [
        (pos + Coord(0,-1), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos + Coord(0,-2), MapTile(_fixed=True,_walls=set(["L","R","D"]))),
        (pos + Coord(0,-3), MapTile(_fixed=True,_walls=set(["L","U","R"]))),
        (pos + Coord(1,-3), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["U"]))),
    ]

def spore_spawn_bboxes(pos, dims):
    return [
        Rect(pos + Coord(0,-3), pos + Coord(1,0)),
        Rect(pos + Coord(1,-3), pos + Coord(2,-2))
    ]

def crocomire_boss_area(pos, dims):
    """Returns the Crocomire Boss Area cmap."""
    return [
        (pos + Coord(-4, 1),MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos + Coord(-3, 1),MapTile(_fixed=True,_walls=set(["L","U","D"]))),
        (pos + Coord(-2, 1),MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + Coord(-1, 1),MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + Coord(0, 1),MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + Coord(1, 1),MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + Coord(2, 1),MapTile(_fixed=True,_item=True,_walls=set(["U","D"]))),
        (pos + Coord(3, 1),MapTile(_fixed=True,_walls=set(["U","D"]))),
        (pos + Coord(4, 1),MapTile(_fixed=True,_item=True,_walls=set(["U","R","D"]))),
        (pos, MapTile(_walls=set(["D"]))),
    ]

def crocomire_bboxes(pos, dims):
    return [
        Rect(pos + Coord(-3,1), pos + Coord(5,2)),
        Rect(pos + Coord(-4,1), pos + Coord(-3,2))
    ]

def botwoon_boss_area(pos, dims):
    """Returns the Botwoon Boss Area cmap."""
    return [
        (pos + Coord(1,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos + Coord(2,0), MapTile(_fixed=True,_walls=set(["L","U","R","D"]))),
        (pos + Coord(3,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["R"]))),
    ]

def botwoon_bboxes(pos, dims):
    return [
        Rect(pos + Coord(1,0), pos + Coord(3,1)),
        Rect(pos + Coord(3,0), pos + Coord(4,1))
    ]

def golden_torizo_boss_area(pos, dims):
    """Returns the Golden Torizo Boss Area cmap."""
    return [
        (pos + Coord(1,0), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos + Coord(2,0), MapTile(_fixed=True,_item=True,_walls=set(["U","R"]))),
        (pos + Coord(1,1), MapTile(_fixed=True,_walls=set(["L","D"]))),
        (pos + Coord(2,1), MapTile(_fixed=True,_walls=set(["R","D"]))),
        (pos + Coord(3,1), MapTile(_fixed=True,_item=True,_walls=set(["L","U","R","D"]))),
        (pos, MapTile(_walls=set(["R"]))),
    ]

def golden_torizo_bboxes(pos, dims):
    return [
        Rect(pos + Coord(1,0), pos + Coord(3,2)),
        Rect(pos + Coord(3,1), pos + Coord(4,2))
    ]

def elevator_down_area(pos, dims):
    """Returns the cmap for a down elevator."""
    e_tiles = [
        (pos, MapTile(_walls=set(["D"]))),
        (pos + Coord(0,1), MapTile(TileType.elevator_main_down,_fixed=True,_walls=set(["L","R","U"]))),
        (pos + Coord(0,2), MapTile(TileType.elevator_shaft,_fixed=True,_walls=set(["L","R"]))),
        (pos + Coord(0,3), MapTile(TileType.up_arrow,_fixed=True,_walls=set(["L","R","D"]))),
    ]
    # Blank tiles down to the bottom of dims
    # Note: range(x,y) = [] when x>=y
    #TODO: dims.y + 1? is dims inclusive?
    for i in range(pos.y + 4, dims.y):
        t = (Coord(pos.x, i), MapTile(TileType.blank,_fixed=True))
        e_tiles.append(t)
    return e_tiles

def elevator_down_bboxes(pos, dims):
    return [
        Rect(pos + Coord(0,1), pos + Coord(1,4)),
    ]

def elevator_up_area(pos, dims):
    """Returns the cmap for an up elevator."""
    e_tiles = [
        (pos, MapTile(_walls=set(["U"]))),
        (pos + Coord(0,-1), MapTile(TileType.elevator_main_down,_fixed=True,_walls=set(["L","R","D"]))),
        (pos + Coord(0,-2), MapTile(TileType.elevator_shaft,_fixed=True,_walls=set(["L","R"]))),
        (pos + Coord(0,-3), MapTile(TileType.up_arrow,_fixed=True,_walls=set(["L","R","U"]))),
    ]
    # Blank tiles up to the top of dims
    for i in range(0, pos.y - 3):
        t = (Coord(pos.x, i), MapTile(TileType.blank,_fixed=True))
        e_tiles.append(t)
    return e_tiles

def elevator_up_bboxes(pos, dims):
    return [
        Rect(pos + Coord(0,-3), pos + Coord(1,0))
    ]

def save_point_area(pos, dims):
    return [
        (pos, MapTile(_save=True))
    ]

#TODO?
def save_point_bboxes(pos, dims):
    return []

def item_area(pos, dims):
    return [
        (pos, MapTile(_item=True))
    ]

def item_bboxes(pos, dims):
    return []

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

# node -> elevators -> (pos -> dims -> tile list)
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
    #TODO: How to connect up the back end?
    elif node == "Mother_Brain":
        return mother_brain_boss_area
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

def node_to_info(node, pos, dims, up_es, down_es):
    if node in up_es:
        return (mk_area(pos, dims, elevator_up_area),
            elevator_up_bboxes(pos, dims))
    elif node in down_es:
        return (mk_area(pos, dims, elevator_down_area),
            elevator_down_bboxes(pos, dims))
    elif node == "Kraid":
        return (mk_area(pos, dims, kraid_boss_area),
            kraid_bboxes(pos, dims))
    elif node == "Phantoon":
        return (mk_area(pos, dims, phantoon_boss_area),
            phantoon_bboxes(pos, dims))
    elif node == "Draygon":
        return (mk_area(pos, dims, draygon_boss_area),
            draygon_bboxes(pos, dims))
    elif node == "Ridley":
        return (mk_area(pos, dims, ridley_boss_area),
            ridley_bboxes(pos, dims))
    elif node == "Mother_Brain":
        return (mk_area(pos, dims, mother_brain_boss_area),
            mother_brain_bboxes(pos, dims))
    elif node == "Bomb_Torizo":
        return (mk_area(pos, dims, bomb_torizo_boss_area),
        bomb_torizo_bboxes(pos, dims))
    elif node == "Spore_Spawn":
        return (mk_area(pos, dims, spore_spawn_boss_area),
            spore_spawn_bboxes(pos, dims))
    elif node == "Botwoon":
        return (mk_area(pos, dims, botwoon_boss_area),
            botwoon_bboxes(pos, dims))
    elif node == "Golden_Torizo":
        return (mk_area(pos, dims, golden_torizo_boss_area),
            golden_torizo_bboxes(pos, dims))
    #TODO - save points, reserves, etc?
    else:
        return (mk_area(pos, dims, item_area),
            item_bboxes(pos, dims))
