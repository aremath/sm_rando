
import functools
from data_types import item_set
from world_rando.coord import Coord
from world_rando.rules import SamusState, SamusPose, Velocity, VType, HVelocity

item_bits = {
    0x1 : "V",
    0x2 : "SPB",
    0x4 : "MB",
    0x8 : "SA",
    0x20 : "GS",
    0x100 : "HJ",
    0x200 : "SJ",
    0x1000 : "B",
    0x2000 : "SB",
    0x4000 : "G",
    0x8000 : "XR"
}

beam_bits = {
    0x1 : "WB",
    0x2 : "IB",
    0x4 : "Spazer",
    0x8 : "PLB",
    0x1000 : "CB"
}

def from_bitflag(flag, flag_dict):
    items = []
    for k,v in flag_dict.items():
        if flag & k:
            items.append(v)
    return item_set.ItemSet(items)

#$079F: Area index
#{
#    0: Crateria
#    1: Brinstar
#    2: Norfair
#    3: Wrecked Ship
#    4: Maridia
#    5: Tourian
#    6: Ceres
#    7: Debug
#}

# Bosses defeated - info not obtained by current data collection!
#         $7E:D828..2F: Boss bits. Indexed by area
#        {
#            1: Area boss (Kraid, Phantoon, Draygon, both Ridleys)
#            2: Area mini-boss (Spore Spawn, Botwoon, Crocomire, Mother Brain)
#            4: Area torizo (Bomb Torizo, Golden Torizo)
#        }
# Region -> (Boss, Miniboss, Torizo)
boss_info = {
    "Crateria": (None, None, None), # Bomb_Torizo is here, but not an item definition
    "Brinstar": ("Kraid", "Spore_Spawn", None),
    "Norfair": ("Ridley", "Crocomire", "Golden_Torizo"),
    "Wrecked_Ship": ("Phantoon", None, None),
    "Maridia": ("Draygon", "Botwoon", None),
    "Tourian": (None, "Mother_Brain", None), # Yes, Mother Brain is a miniboss
    #"Ceres": ("Ceres_Ridley", None, None), # Ceres_Ridley is an item definition, but causes problems
    "Ceres": (None, None, None), # Ceres_Ridley is an item definition, but causes problems
    "Debug": (None, None, None)
}

def abstractify_boss_info(frame, offset=0xd7c0):
    frame8 = frame.view("uint8")
    items = []
    # Process relevant events
    if frame8[offset + 0x61] & 0x20:
        items.append("Shaktool")
    if frame8[offset + 0x61] & 0x10:
        items.append("Drain")
    # Process boss bits
    for i, (region, info) in enumerate(boss_info.items()):
        info_bits = frame8[offset + 0x68 + i]
        for j in range(3):
            if info_bits & 2**j and info[j] is not None:
                items.append(info[j])
    return item_set.ItemSet(items)

def abstractify_items(frame):
    items = from_bitflag(frame[0x09a4 // 2], item_bits)
    beams = from_bitflag(frame[0x09a8 // 2], beam_bits)
    all_items = items | beams
    n_ammo = 0
    # Missiles
    max_missiles = frame[0x09c8 // 2]
    n_ammo += max_missiles // 5
    if max_missiles > 0:
        all_items = all_items.add("M")
    # Supers
    max_supers = frame[0x09cc // 2]
    n_ammo += max_supers // 5
    if max_supers > 0:
        all_items = all_items.add("S")
    # PBs
    max_pbs = frame[0x09ce // 2]
    n_ammo += max_pbs // 5
    if max_pbs > 0 :
        all_items = all_items.add("PB")
    # Etanks
    max_energy = frame[0x09c4 // 2]
    n_ammo += (max_energy - 99) // 100
    if max_energy > 99:
        all_items = all_items.add("E")
    return all_items, n_ammo
 
# Within-room pos rather than "global" pos using maptiles
def abstractify_pos(frame):
    # Compute Abstract position
    x_radius = frame[0x0afe // 2]
    y_radius = frame[0x0b00 // 2]
    x_center = frame[0x0af6 // 2]
    y_center = frame[0x0afa // 2]
    top = (y_center - y_radius) // 16
    left = (x_center - x_radius) // 16
    pos = Coord(left, top)
    return pos

# Use global position for shared reference point
#$079F: Area index
#{
#    0: Crateria
#    1: Brinstar
#    2: Norfair
#    3: Wrecked Ship
#    4: Maridia
#    5: Tourian
#    6: Ceres
#    7: Debug
#}
area_offsets = {
    0: Coord(3, 10),
    1: Coord(0, 29),
    2: Coord(31, 49),
    3: Coord(37, 0),
    4: Coord(28, 29),
    5: Coord(0, 10),
    # Out of bounds
    6: Coord(0, -10),
    7: Coord(0, 0),
}

#maptile_size = Coord(256, 256)
# In integer positions, 256 in pixel positions
maptile_size = Coord(16, 16)

# Global pos
def abstractify_pos_global(frame):
    frame8 = frame.view("uint8")
    # Area pos
    area_index = frame8[0x79f]
    area_pos = maptile_size * area_offsets[area_index]
    # Map pos
    map_x = frame8[0x07a1]
    map_y = frame8[0x07a3]
    map_pos = maptile_size * Coord(map_x, map_y)
    # Room pos
    room_pos = abstractify_pos(frame)
    return area_pos + map_pos + room_pos

def abstractify_pose(frame):
    x_radius = frame[0x0afe // 2]
    y_radius = frame[0x0b00 // 2]
    # Compute abstract pose
    if y_radius <= 0x7:
        pose = SamusPose.MORPH
    elif y_radius == 0x0a:
        pose = SamusPose.JUMP
    elif y_radius == 0x0c:
        pose = SamusPose.SPIN
    #TODO! Add Crouch pose & rules
    elif y_radius == 0x10:
        pose = SamusPose.MORPH
    #TODO: unknown pose
    elif y_radius == 0x11:
        pose = SamusPose.MORPH
    elif y_radius == 0x13:
        pose = SamusPose.JUMP
    elif y_radius == 0x15:
        pose = SamusPose.STAND
    #TODO: unknown pose
    elif y_radius == 0x18:
        pose = SamusPose.STAND
    return pose
    
#TODO
def abstractify_velocity(frame):
    hvel = HVelocity(VType.RUN, 0)
    vvel = 0
    return Velocity(vvel, hvel)

def abstractify_state(frame, global_pos=False):
    if global_pos:
        pos = abstractify_pos_global(frame)
    else:
        pos = abstractify_pos(frame)
    pose = abstractify_pose(frame)
    v = abstractify_velocity(frame)
    items, n_ammo = abstractify_items(frame)
    return SamusState(pos, v, items, pose)

def state_distance(state1, state2, offset):
    if state1.items == state2.items:
        return state1.position.euclidean(state2.position + offset)
    else:
        return float("inf")

def state_set_distance(state1, state_lib, offset):
    dists = [(state_distance(state1, s, offset), s) for s in state_lib]
    return min(dists, key=lambda x: x[0])

def mk_cell_ok(state_library, max_distance, offset):
    """
    Make a function that returns True iff samus is inside the guidance tube
    """
    @functools.lru_cache(maxsize=None)
    def cell_ok(state):
        dist = state_set_distance(state, state_library, offset)[0]
        return dist <= max_distance
    return cell_ok

# Want weight to increase for cells with a lower total distance to goal
# futurecost is a dict of abstract state -> float
# Use with go_explore.softminselector
def mk_cell_dists(state_library, futurecost, offset):
    @functools.lru_cache(maxsize=None)
    def cell_dist(state):
        # Approximate distance to the nearest valid state
        dist_to_valid, valid = state_set_distance(state, state_library, offset)
        # Approximate futurecost to reach the goal from valid
        dist_to_goal = futurecost[valid]
        totaldist = dist_to_valid + dist_to_goal
        return totaldist
    return cell_dist
