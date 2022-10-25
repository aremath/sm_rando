
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

#TODO: bosses defeated - info not obtained by current data collection!
#         $7E:D828..2F: Boss bits. Indexed by area
#        {
#            1: Area boss (Kraid, Phantoon, Draygon, both Ridleys)
#            2: Area mini-boss (Spore Spawn, Botwoon, Crocomire, Mother Brain)
#            4: Area torizo (Bomb Torizo, Golden Torizo)
#        }

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
 
#TODO: - this uses within-room pos rather than "global" pos using maptiles
def abstractify_pos_pose(frame):
    # Compute Abstract position
    x_center = frame[0x0af6 // 2]
    y_center = frame[0x0afa // 2]
    x_radius = frame[0x0afe // 2]
    y_radius = frame[0x0b00 // 2]
    top = (y_center - y_radius) // 16
    left = (x_center - x_radius) // 16
    pos = Coord(left, top)
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
    return pos, pose
    
#TODO
def abstractify_velocity(frame):
    hvel = HVelocity(VType.RUN, 0)
    vvel = 0
    return Velocity(vvel, hvel)

def abstractify_state(frame):
    pos, pose = abstractify_pos_pose(frame)
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
def mk_cell_dists(state_library, futurecost):
    @functools.lru_cache(maxsize=None)
    def cell_dist(state):
        # Approximate distance to the nearest valid state
        dist_to_valid, valid = state_set_distance(state, state_library, offset)
        # Approximate futurecost to reach the goal from valid
        dist_to_goal = futurecost[valid]
        totaldist = dist_to_valid + dist_to_goal
        return totaldist
    return cell_dist
