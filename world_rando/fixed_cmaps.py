from functools import reduce

from world_rando.coord import *
from world_rando.concrete_map import *
from world_rando.room_dtypes import Room, Door, Converter, DetailCopyConverter
from world_rando.item_order_graph import NodeType

#TODO: how to make sure we generate the Kraid and Draygon item rooms?
#TODO: these functions should return a cmap, a list of implicit doors, and a list of implicit rooms.
#   Implicit Doors should be added to the appropriate room
#   Implicit Rooms should be able to be converted to rom data structures somehow
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
    if bounded_put_check(cmap, tile_list):
        return cmap
    else:
        return None

def default_mk_room(loc, rooms, tile_rooms):
    return

def mk_copyconverter(room_name):
    return lambda p: DetailCopyConverter(room_name, p)

rhs = "room_header_{}"
boss_rooms = {
    "Kraid"         :   rhs.format("0x7a59f"),
    "Phantoon"      :   rhs.format("0x7cd13"),
    "Draygon"       :   rhs.format("0x7da60"),
    "Ridley"        :   rhs.format("0x7b32e"),
    "Bomb_Torizo"   :   rhs.format("0x79804"),
    "Spore_Spawn"   :   rhs.format("0x79dc7"),
    "Botwoon"       :   rhs.format("0x7d95e"),
    "Golden_Torizo" :   rhs.format("0x7b283"),
    "Mother_Brain"  :   rhs.format("0x7dd58"),
}

#TODO: how to do Bomb Torizo's item?
#TODO: other bosses
boss_item_rooms = {
    "Kraid"         :   rhs.format("0x7a6e2"),
    "Draygon"       :   rhs.format("0x7d9aa"),
    "Ridley"        :   rhs.format("0x7B698"),
}


# Functions for instantiating rooms for a boss area
def mk_single_mker(boss_name, boss_loc):
    bo_dir = -boss_loc
    def mker(loc, rooms, tile_rooms):
        outside = tile_rooms[loc]
        boss_id = f"{boss_name}_Boss"
        boss_id_to_outside = Door(loc + boss_loc, bo_dir, boss_id, outside, f"{boss_name}_bo")
        outside_to_boss_id = Door(loc, -bo_dir, outside, boss_id, f"{boss_name}_ob")
        boss_room = Room(None, Coord(1,1), boss_id, loc + boss_loc)
        boss_room.converter = mk_copyconverter(boss_rooms[boss_name])
        boss_room.doors.append(boss_id_to_outside)
        rooms[outside].doors.append(outside_to_boss_id)
        rooms[boss_id] = boss_room
    return mker

# Fill-in-the-blanks maker for boss rooms
def mk_item_mker(boss_name, boss_size, item_size, boss_loc, item_loc, ob_dir=None):
    ib_loc = item_loc
    ibx = (item_loc - boss_loc).x
    ib_dir = Coord(ibx // abs(ibx), 0)
    bi_loc = item_loc + ib_dir
    bi_dir = -ib_dir
    if ob_dir is None:
        box = boss_loc.x
        ob_dir = Coord(box // abs(box), 0)
    ob_loc = Coord(0,0)
    bo_dir = -ob_dir
    bo_loc = ob_loc + ob_dir
    def mker(loc, rooms, tile_rooms):
        outside = tile_rooms[loc]
        boss_id = f"{boss_name}_Boss"
        item_id = f"{boss_name}_Item"
        b_to_i = Door(loc + bi_loc, bi_dir, boss_id, item_id, f"{boss_name}_bi")
        i_to_b =  Door(loc + ib_loc, ib_dir, item_id, boss_id, f"{boss_name}_ib")
        b_to_outside = Door(loc + bo_loc, bo_dir, boss_id, outside, f"{boss_name}_bo")
        outside_to_b = Door(loc + ob_loc, ob_dir, outside, boss_id, f"{boss_name}_ob")
        boss_room = Room(None, boss_size, boss_id, loc + boss_loc)
        #TODO: how to specify what should be kept and what should be replaced?
        boss_room.converter = mk_copyconverter(boss_rooms[boss_name])
        boss_room.doors.append(b_to_i)
        boss_room.doors.append(b_to_outside)
        item_room = Room(None, item_size, item_id, loc + item_loc)
        item_room.level = item_id
        item_room.converter = mk_copyconverter(boss_item_rooms[boss_name])
        item_room.doors.append(i_to_b)
        #TODO: Add gadora PLM to outside_room
        #TODO: How to tell outside room about using gadora tiles near the gadora??
        rooms[outside].doors.append(outside_to_b)
        rooms[boss_id] = boss_room
        rooms[item_id] = item_room
    return mker

#TODO: FixedMap objects implement a constraintgraph and create implicit actions in the 
# map generation search space (create, and move across)
#TODO: FixedMap objects contain Room objects that are created when the FixedMap is used,
# and refer to each other -> "Room" constructors? Functions that return Rooms when given data?
# Allows room generation to be initialized at any stage
# FixedMaps:
# - Fixed Concrete Map Definition
# - Fixed Room Bounding Boxes
# - Fixed ConstraintGraph implemented by the FixedMap
# - Info -> [Room] special generation function
#TODO: what needs to be in Info?
# Needs at least the map position and the dict mapping coords to rooms (to instantiate doors)
class FixedMap(object):

    def __init__(self, tile_list, bboxes, mk_room=default_mk_room,
            extend=None, dims=None,):
        self.real_cmap = ConcreteMap(dims)
        if not bounded_put_check(self.real_cmap, tile_list):
            assert False
        # What room bounding boxes does the fixedmap contain?
        self.bboxes = bboxes
        # How far does this room extend up or down (how does it affect the cmap?)
        self.extend = extend
        # A function that takes info about where the fixed was placed and creates the implicit rooms
        # needed to implement that cmap by using side-effects to alter the relevant data structures
        #TODO: mk_rooms()?
        self.mk_room = mk_room

    def cmap(self, pos, dims):
        if self.extend is None:
            return self.real_cmap
        # For elevators, extend them downwards or upwards with blank fixed tiles
        elif self.extend > 0:
            c2 = ConcreteMap(None, _tiles=self.real_cmap.tiles)
            for i in range(self.extend, dims.y - pos.y):
                c2[Coord(0, i)] = MapTile(TileType.elevator_shaft,_fixed=True)
            return c2
        elif self.extend <= 0:
            c2 = ConcreteMap(None, _tiles=self.real_cmap.tiles)
            for i in range(-pos.y, self.extend):
                c2[Coord(0, i)] = MapTile(TileType.elevator_shaft,_fixed=True)
            return c2

# Kraid
kraid_tiles = [
        (Coord(1,0), MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(0,1)]))),
        (Coord(1,-1), MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(0,-1)]))),
        (Coord(2,0), MapTile(_fixed=True,_walls=set([Coord(1,0),Coord(0,1)]))),
        (Coord(2,-1), MapTile(_fixed=True,_walls=set([Coord(1,0),Coord(0,-1)]))),
        (Coord(3,0), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(1,0)]))),
    ]
kraid_bboxes = [
        Rect(Coord(1,-1), Coord(3,1)),
        Rect(Coord(3,0), Coord(4,1))
        ]
mk_kraid = mk_item_mker("Kraid", Coord(2,2), Coord(1,1), Coord(1,0), Coord(3,1))
kraid_room = FixedMap(kraid_tiles, kraid_bboxes, mk_kraid)

# Phantoon
phantoon_tiles = [
        (Coord(1,0), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(1,0)])))
        ]

phantoon_bboxes = [
        Rect(Coord(1,0), Coord(2,1))
        ]
mk_phantoon = mk_single_mker("Phantoon", Coord(1,0))
phantoon_room = FixedMap(phantoon_tiles, phantoon_bboxes, mk_phantoon)

# Draygon
draygon_tiles = [
        (Coord(-1,0), MapTile(_fixed=True,_walls=set([Coord(1,0),Coord(0,-1)]))),
        (Coord(-1,1), MapTile(_fixed=True,_walls=set([Coord(1,0),Coord(0,1)]))),
        (Coord(-2,0), MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(0,-1)]))),
        (Coord(-2,1), MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(0,1)]))),
        (Coord(-3,1), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(-1,0)]))),
    ]

draygon_bboxes = [
        Rect(Coord(-2,0), Coord(0,2)),
        Rect(Coord(-3,1), Coord(-2,2))
    ]
mk_draygon = mk_item_mker("Draygon", Coord(2,2), Coord(1,1), Coord(-2, 0), Coord(-3,1))
draygon_room = FixedMap(draygon_tiles, draygon_bboxes, mk_draygon)

# Ridley
ridley_tiles = [
        (Coord(-1,0), MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0)]))),
        (Coord(-1,1), MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(1,0),Coord(0,1)]))),
        (Coord(-2,1), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(-1,0)]))),

    ]

ridley_bboxes = [
        Rect(Coord(-1,0), Coord(0,2)),
        Rect(Coord(-2,1), Coord(-1,2))
    ]
mk_ridley = mk_item_mker("Ridley", Coord(1,2), Coord(1,1), Coord(-1,0), Coord(-2,1))
ridley_room = FixedMap(ridley_tiles, ridley_bboxes, mk_ridley)

# Mother Brain
#TODO: how to make sure that the other side is used?
mother_brain_tiles = [
        (Coord(-1,0), MapTile(_fixed=True,_walls=set([Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(-2,0), MapTile(_fixed=True,_walls=set([Coord(0,-1),Coord(0,1)]))),
        (Coord(-3,0), MapTile(_fixed=True,_walls=set([Coord(0,-1),Coord(0,1)]))),
        (Coord(-4,0), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(0,1)]))),
        (Coord(-5,0), MapTile(_walls=set([Coord(1,0)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(-1,0)]))),
    ]

mother_brain_bboxes = [
        Rect(Coord(-4,0), Coord(0,1)),
    ]
#TODO: mk_mother_brain
mother_brain_room = FixedMap(mother_brain_tiles, mother_brain_bboxes)

# Bomb Torizo
bomb_torizo_tiles = [
        (Coord(1,0), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(1,0)]))),
        ]

bomb_torizo_bboxes = [
        Rect(Coord(1,0), Coord(2,1)),
        ]
mk_bomb_torizo = mk_single_mker("Bomb_Torizo", Coord(1,0))
bomb_torizo_room = FixedMap(bomb_torizo_tiles, bomb_torizo_bboxes)

# Spore Spawn
spore_spawn_tiles = [
        (Coord(0,-1), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,-2), MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(1,0),Coord(0,1)]))),
        (Coord(0,-3), MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0)]))),
        (Coord(1,-3), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(0,-1)]))),
        ]

spore_spawn_bboxes = [
        Rect(Coord(0,-3), Coord(1,0)),
        Rect(Coord(1,-3), Coord(2,-2))
        ]
mk_spore_spawn = mk_item_mker("Spore_Spawn", Coord(1,2), Coord(1,1), Coord(0,-2), Coord(1,-2), Coord(0,-1))
spore_spawn_room = FixedMap(spore_spawn_tiles, spore_spawn_bboxes, mk_spore_spawn)

# Crocomire
crocomire_tiles = [
        (Coord(-4, 1),MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(-3, 1),MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(0,1)]))),
        (Coord(-2, 1),MapTile(_fixed=True,_walls=set([Coord(0,-1),Coord(0,1)]))),
        (Coord(-1, 1),MapTile(_fixed=True,_walls=set([Coord(0,-1),Coord(0,1)]))),
        (Coord(0, 1),MapTile(_fixed=True,_walls=set([Coord(0,-1),Coord(0,1)]))),
        (Coord(1, 1),MapTile(_fixed=True,_walls=set([Coord(0,-1),Coord(0,1)]))),
        (Coord(2, 1),MapTile(_fixed=True,_item=True,_walls=set([Coord(0,-1),Coord(0,1)]))),
        (Coord(3, 1),MapTile(_fixed=True,_walls=set([Coord(0,-1),Coord(0,1)]))),
        (Coord(4, 1),MapTile(_fixed=True,_item=True,_walls=set([Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(0,1)]))),
        ]

crocomire_bboxes = [
        Rect(Coord(-3,1), Coord(5,2)),
        Rect(Coord(-4,1), Coord(-3,2))
        ]
mk_crocomire = mk_item_mker("Crocomire", Coord(8,1), Coord(1,1), Coord(-3,1), Coord(-4,1), Coord(0,1))
crocomire_room = FixedMap(crocomire_tiles, crocomire_bboxes, mk_crocomire)

# Botwoon
botwoon_tiles = [
        (Coord(1,0), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(2,0), MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(3,0), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(1,0)]))),
        ]

botwoon_bboxes = [
        Rect(Coord(1,0), Coord(3,1)),
        Rect(Coord(3,0), Coord(4,1))
        ]
mk_botwoon = mk_item_mker("Botwoon", Coord(2,1), Coord(1,1), Coord(1,0), Coord(3,0))
botwoon_room = FixedMap(botwoon_tiles, botwoon_bboxes, mk_botwoon)

# Golden Torizo

golden_torizo_tiles = [
        (Coord(1,0), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(2,0), MapTile(_fixed=True,_item=True,_walls=set([Coord(0,-1),Coord(1,0)]))),
        (Coord(1,1), MapTile(_fixed=True,_walls=set([Coord(-1,0),Coord(0,1)]))),
        (Coord(2,1), MapTile(_fixed=True,_walls=set([Coord(1,0),Coord(0,1)]))),
        (Coord(3,1), MapTile(_fixed=True,_item=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(1,0)]))),
        ]

golden_torizo_bboxes = [
        Rect(Coord(1,0), Coord(3,2)),
        Rect(Coord(3,1), Coord(4,2))
        ]

mk_golden_torizo = mk_item_mker("Golden_Torizo", Coord(2,2), Coord(1,1), Coord(1,0), Coord(3,1))
golden_torizo_room = FixedMap(golden_torizo_tiles, golden_torizo_bboxes, mk_golden_torizo)

# Elevator Down

elevator_down_tiles = [
        (Coord(0,0), MapTile(_walls=set([down]))),
        (Coord(0,1), MapTile(TileType.elevator_main_down,_fixed=True,_walls=set([left,right,up]))),
        (Coord(0,2), MapTile(TileType.elevator_shaft,_fixed=True,_walls=set([left,right]))),
        (Coord(0,3), MapTile(TileType.up_arrow,_fixed=True,_walls=set([left,right,down]))),
        ]

elevator_down_bboxes = [
        Rect(Coord(0,1), Coord(1,4)),
        ]

elevator_down_room = FixedMap(elevator_down_tiles, elevator_down_bboxes, extend=4)

# Elevator Up

elevator_up_tiles = [
        (Coord(0,0), MapTile(_walls=set([up]))),
        (Coord(0,-1), MapTile(TileType.elevator_main_down,_fixed=True,_walls=set([left,right,down]))),
        (Coord(0,-2), MapTile(TileType.elevator_shaft,_fixed=True,_walls=set([left, right]))),
        (Coord(0,-3), MapTile(TileType.up_arrow,_fixed=True,_walls=set([left, right, up]))),
        ]

elevator_up_bboxes = [
        Rect(Coord(0,-3), Coord(1,0))
        ]

elevator_up_room = FixedMap(elevator_up_tiles, elevator_up_bboxes, extend=-3)

# Save Point
#TODO: How to allow save points to have either left or right doors, but not up / down doors?
#   Eventually, save points will have two fixedmaps, and the search will be responsible for choosing one of them
save_point_tiles = [
        (Coord(1,0), MapTile(_fixed=True,_save=True,_walls=set([Coord(-1,0),Coord(0,-1),Coord(1,0),Coord(0,1)]))),
        (Coord(0,0), MapTile(_walls=set([Coord(1,0)])))
        ]

save_point_bboxes = [
        Rect(Coord(1,0), Coord(2,1))
        ]

#TODO: mk_save_point
save_point_room = FixedMap(save_point_tiles, save_point_bboxes)

# Item - Is this a fixedmap, or something else?
item_tiles = [
        (Coord(0,0), MapTile(_item=True))
        ]

item_bboxes = []

item_room = FixedMap(item_tiles, item_bboxes)

fixed_maps = {
    "Kraid"         :   kraid_room,
    "Phantoon"      :   phantoon_room,
    "Draygon"       :   draygon_room,
    "Ridley"        :   ridley_room,
    "Bomb_Torizo"   :   bomb_torizo_room,
    "Spore_Spawn"   :   spore_spawn_room,
    "Botwoon"       :   botwoon_room,
    "Golden_Torizo" :   golden_torizo_room,
    "Mother_Brain"  :   mother_brain_room,
}

def node_to_fixedmap(node, node_type):
    if node_type == NodeType.ELEVATOR_UP:
        return elevator_up_room
    elif node_type == NodeType.ELEVATOR_DOWN:
        return elevator_down_room
    elif node in fixed_maps:
        return fixed_maps[node]
    #TODO: Ship?
    elif node_type == NodeType.SAVE or node_type == NodeType.SHIP:
        return save_point_room
    #TODO - save points, reserves, map stations, etc?
    else:
        return item_room

