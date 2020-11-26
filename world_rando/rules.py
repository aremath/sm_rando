from PIL import Image
import numpy as np
from enum import IntEnum
from sm_rando.world_rando.coord import Coord, Rect
from sm_rando.data_types.item_set import ItemSet

Infinity = float("inf")
TERMINAL_VELOCITY = 1

# Part 1: Enumerated types
class AbstractTile(IntEnum):
    UNKNOWN = 0
    AIR = 1
    SOLID = 2
    GRAPPLE = 3
    BLOCK_BOMB = 4
    BLOCK_MISSILE = 5
    BLOCK_SUPER = 6
    BLOCK_POWER_BOMB = 7
    BLOCK_GRAPPLE = 8
    BLOCK_SPEED = 9
    BLOCK_CRUMBLE = 10
    BLOCK_SHOT = 11

# Translation between tile colors and types of tile
unknown_color = (255, 255, 255)
player_before_color = (255, 0, 0)
player_after_color = (0, 255, 0)
air_color = (251, 242, 54)
water_color = (48, 185, 211)
solid_color = (0, 0, 0)
grapple_color = (119, 33, 105)
water_air_color = (30, 211, 106)
# Indicate water/air ambiguity AND player presence
player_before_water_air_color = (198, 0, 0)
player_before_water_color = (145, 0, 0)
player_after_water_air_color = (0, 198, 0)
player_after_water_color = (0, 145, 0)
item_color = (255, 22, 169)
# Destructible blocks
block_bomb_color = (141, 73, 154)
block_missile_color = (154, 73, 73)
block_power_bomb_color = (154, 116, 73)
block_super_color = (73, 154, 82)
block_grapple_color = (73, 150, 154)
block_speed_color = (73, 90, 154)
block_crumble_color = (107, 154, 73)
block_shot_color = (154, 150, 73)

abstract_to_color = {
    AbstractTile.UNKNOWN : unknown_color,
    AbstractTile.AIR : air_color,
    AbstractTile.SOLID : solid_color,
    AbstractTile.GRAPPLE : grapple_color,
    AbstractTile.BLOCK_BOMB : block_bomb_color,
    AbstractTile.BLOCK_MISSILE : block_missile_color,
    AbstractTile.BLOCK_SUPER : block_super_color,
    AbstractTile.BLOCK_POWER_BOMB : block_power_bomb_color,
    AbstractTile.BLOCK_GRAPPLE : block_grapple_color,
    AbstractTile.BLOCK_SPEED : block_speed_color,
    AbstractTile.BLOCK_CRUMBLE : block_crumble_color,
    AbstractTile.BLOCK_SHOT : block_shot_color
    }

class SamusPose(IntEnum):
    STAND = 0
    MORPH = 1
    JUMP = 2
    SPIN = 3

class LiquidType(IntEnum):
    NONE = 0
    WATER = 1
    LAVA = 2
    ACID = 3

class VType(IntEnum):
    # Special "untyped" zero velocity
    RUN = 1
    SPEED = 2
    WATER = 3

# The number of tiles to run when you reach maximum horizontal velocity
velocity_maxima = {
    VType.RUN: 4,
    VType.SPEED: 30,
    VType.WATER: 5
        }

class VBehavior(IntEnum):
    STORE = 0
    LOSE = 1

class Interval(object):

    def __init__(self, left, right):
        assert left <= right
        self.left = left
        self.right = right

    def __contains__(self, n):
        return self.left <= n and n <= self.right

    def flip(self):
        """ Horizontally flip """
        return Interval(-self.right, -self.left)

    @property
    def size(self):
        return self.right - self.left

    def shift(self, n):
        return Interval(self.left + n, self.right + n)

    def interval_image(self, n, behavior):
        if behavior is VBehavior.LOSE:
            return Interval(n, n)
        elif behavior is VBehavior.STORE:
            return self.shift(n)
        else:
            assert False

    def __eq__(self, other):
        return self.left == other.left and self.right == other.right

    def subset(self, other):
        l = self.l >= other.l
        r = self.r <= other.r
        return l and r

    def intersect(self, other):
        l = max(self.left, other.left)
        r = min(self.right, other.right)
        # Set may be empty
        if l > r:
            return None
        else:
            return Interval(l, r)

    def horizontal_flip(self):
        return Interval(-self.right, -self.left)

    def copy(self):
        return Interval(self.left, self.right)

    def __repr__(self):
        return "i({}, {})".format(self.left, self.right)

class HVelocitySet(object):

    def __init__(self, types, interval):
        self.types = types
        self.interval = interval

    def __contains__(self, hvel):
        if hvel.type in self.types:
            return hvel.value in self.interval
        else:
            return hvel.value == 0 and 0 in self.interval

    def shift(self, hvel):
        if hvel.type in types or hvel.value == 0:
            i = self.interval.shift(hvel.value)
            return HVelocitySet(self.types, i)
        # Inherit the type if the velocity is only zero
        elif self.interval == Interval(0,0):
            return HVelocitySet(frozenset([hvel.type]), Interval(hvel.value, hvel.value))
        else:
            return None

    def interval_image(self, vh, behavior):
        if behavior is VBehavior.LOSE:
            return HVelocitySet(frozenset([vh.type]), Interval(vh.value, vh.value))
        elif behavior is VBehavior.STORE:
            return self.shift(vh)
        else:
            assert False

    def subset(self, other):
        # Type doesn't matter if the interval covers only zero
        if self.types <= other.types or self.interval == Interval(0,0):
            return self.interval.subset(other.interval)
        else:
            return False

    def intersect(self, other):
        i = self.interval.intersect(other.interval)
        t = self.t & other.t
        if i is None or len(t) == 0:
            return None
        else:
            return HVelocitySet(t, i)

    def horizontal_flip(self):
        t = self.types.copy()
        return HVelocitySet(t, self.interval.horizontal_flip())

class VelocitySet(object):
    
    def __init__(self, vertical_interval, horizontal_set):
        self.vertical_set = vertical_interval
        self.horizontal_set = horizontal_set

    def __contains__(self, velocity):
        v = velocity.vv in self.vertical_set
        h = velocity.vh in self.horizontal_set
        return v and h

    def shift(self, velocity):
        v = vertical_set.shift(velocity.vv)
        h = horizontal_set.shift(velocity.vh)
        assert h is not None
        return VelocitySet(v,h)

    def subset(self, other):
        v = self.vertical_set.subset(other.vertical_set)
        h = self.horizontal_set.subset(other.horizontal_set)
        return v and h

    def intersect(self, other):
        v = self.vertical_set.intersect(other.vertical_set)
        h = self.horizontal_set.intersect(other.horizontal_set)
        if v is None or h is None:
            return None
        else:
            return VelocitySet(v, h)

    def horizontal_flip(self):
        return VelocitySet(self.vertical_set.copy(), self.horizontal_set.horizontal_flip())

class VelocityFunction(object):

    def __init__(self, domain, vertical_b, horizontal_b, vadd):
        self.domain = domain
        self.vertical_behavior = vertical_b
        self.horizontal_behavior = horizontal_b
        self.vadd = vadd

    def apply(self, velocity):
        """ Apply to get a new velocity. None if the parameter is not in the domain """
        if velocity in self.domain:
            start_vel = velocity.copy()
            if self.vertical_behavior is VBehavior.LOSE:
                start_vel.vv = 0
            if self.horizontal_behavior is VBehavior.LOSE:
                start_vel.vh = HVelocity(VType.RUN, 0)
            return start_vel + self.vadd
        else:
            return None

    @property
    def image(self):
        """ Velocity set which is the image """
        v_interval = self.domain.vertical_set.interval_image(self.vadd.vv, self.vertical_behavior)
        h_interval = self.domain.horizontal_set.interval_image(self.vadd.vh, self.horizontal_behavior)
        return VelocitySet(v_interval, h_interval)

    def preimage(self, vset):
        """ Pre-image of a set under this function """
        assert vset.subset(self.image)
        if self.vertical_behavior is VBehavior.LOSE:
            v_interval = Interval(-Infinity, Infinity)
        else:
            # Going backwards
            v_interval = self.domain.vertical_set.shift(-self.vadd.vv)
        if self.horizontal_behavior is VBehavior.LOSE:
            h_i = Interval(-Infinity, Infinity)
            h_set = frozenset([VType.RUN, VType.SPEED, VType.WATER])
            h_interval = HVelocitySet(h_i, h_set)
        else:
            h_interval = self.domain.horizontal_set.shift(-self.vadd.vh)
        return VelocitySet(v_interval, h_interval)

    def compose(self, other):
        # f x f'
        # The points that f maps to and f' maps from
        agree = self.image.intersect(other.domain)
        # Incompatible functions agree on no points
        if agree is None:
            return None
        # Points that can be mapped from
        p = self.preimage(agree)
        # Points that can be mapped from and are feasible
        domain = p.intersect(self.domain)
        # Incompatible if no points can be mapped from
        if domain is None:
            return None
        vh, hb = combine_vs(self.vadd.vh, other.vadd.vh, self.horizontal_behavior, other.horizontal_behavior)
        vv, vb = combine_vs(self.vadd.vv, other.vadd.vv, self.vertical_behavior, other.vertical_behavior)
        v = Velocity(vv, vh)
        return VelocityFunction(domain, vb, hb, v)

    def horizontal_flip(self):
        domainf = self.domain.horizontal_flip()
        addf = self.vadd.horizontal_flip()
        return VelocityFunction(domainf, self.vertical_behavior, self.horizontal_behavior, addf)

def combine_vs(v1, v2, b1, b2):
    """
    Combine velocities to obtain the result of doing both 'velocity actions'.
    """
    # Neither lose means add both
    if b1 is not VBehavior.LOSE and b2 is not VBehavior.LOSE:
        v = v1 + v2
        b = VBehavior.STORE
    # Second lose means it comes after applying the first,
    # So the intermediate velocity does not matter
    elif b2 is VBehavior.LOSE:
        v = v2
        b = VBehavior.LOSE
    # First lose and NOT second lose means the velocity change from v1 will carry over
    # and combine with v2
    elif b1 is VBehavior.LOSE:
        v = v1 + v2
        b = VBehavior.LOSE
    return v, b

class HVelocity(object):
    
    def __init__(self, vtype, value):
        self.type = vtype
        assert vtype in velocity_maxima
        self.value = value

    def __eq__(self, other):
        # Always must share value
        if self.value == other.value:
            # Type matters unless velocity is zero
            if self.type == other.type or self.value == 0:
                return True
        return False

    def __add__(self, other):
        if self.type == other.type:
            t = self.type
        # Inherit type if value is zero
        elif self.value == 0:
            t = other.type
        elif other.value == 0:
            t = self.type
        # Type mismatch is bad
        else:
            return None
        v = self.value + other.value
        vmax = velocity_maxima[t]
        if v > vmax:
            v = vmax
        elif v < -vmax:
            v = -vmax
        return HVelocity(t, v)

    def __hash__(self):
        return hash((self.type, self.value))

    def flip(self):
        return HVelocity(self.type, -self.value)

    def copy(self):
        return HVelocity(self.type, self.value)

#TODO: what about "underwater" vertical velocity vs. air-based vertical velocity?
#TODO: what about max velocity?
class Velocity(object):

    def __init__(self, vv, vh):
        # Integer
        self.vv = vv
        # (VType, Integer)
        self.vh = vh

    def horizontal_flip(self):
        return Velocity(self.vv, self.vh.flip())

    def __eq__(self, other):
        return self.vv == other.vv and self.vh == other.vh

    def __add__(self, other):
        #TODO: TERMINAL_VELOCITY
        v = self.vv + other.vv
        h = self.vh + other.vh
        assert h is not None
        return Velocity(v, h)

    def __hash__(self):
        return hash((self.vv, self.vh))

    def copy(self):
        hv = self.vh.copy()
        return Velocity(self.vv, hv)

    def __repr__(self):
        return "V: {}, H: {}, {}".format(self.vv, self.vh.type, self.vh.value)

#TODO: to "break" a block, need a set of {pose, item}.
# e.g. to break bomb blocks, need either bombs+mb, pbs+mb (and any pose), or screw + spin
# OR can be a speed! To break speed blocks, need max speedbooster speed or shinespark pose
#TODO: how to handle super block in a tunnel? You don't necessarily need stand to destroy a super block...
#TODO: a "plant power bomb 'action' as part of the BFS? -> a fire super missile action...
# Gets very complex very quickly though...

any_velocity_type = set([VType.RUN, VType.SPEED, VType.WATER])
any_pose = set([SamusPose.STAND, SamusPose.MORPH, SamusPose.JUMP, SamusPose.SPIN])
any_interval = Interval(-Infinity, Infinity)
any_velocity = VelocitySet(any_interval, HVelocitySet(any_velocity_type, any_interval))

# The requirements to treat blocks as solid
# Cannot treat a tile as solid if either it is not in this data structure, or samus does not meet one of
# the necessary requirements
block_solid_requirements = {
        AbstractTile.SOLID : [(any_velocity, ItemSet([]), any_pose)],
        AbstractTile.BLOCK_CRUMBLE: "Reciprocal",
        # Can treat a shot block as either solid or air depending on the situation
        AbstractTile.BLOCK_SHOT : [(any_velocity, ItemSet([]), any_pose)],
}

speed_hv = HVelocitySet(set([VType.SPEED]), Interval(30, Infinity))
# Exposing a weakness of velocity sets as single-sided intervals
speed_velocity_l = VelocitySet(any_interval, speed_hv)
speed_velocity_r = VelocitySet(any_interval, speed_hv.horizontal_flip())
# Negative vertical speed and no horizontal speed
crumble_velocity = VelocitySet(Interval(0, Infinity), HVelocitySet(any_velocity_type, Interval(0,0)))

# The requirements to treat blocks as air
block_air_requirements = {
    AbstractTile.AIR : [(any_velocity, ItemSet([]), any_pose)],
    AbstractTile.BLOCK_BOMB : [(any_velocity, ItemSet(["MB", "B"]), any_pose),
                               (any_velocity, ItemSet(["MB", "PB"]), any_pose),
                               (any_velocity, ItemSet(["SA"]), set([SamusPose.SPIN]))],
    AbstractTile.BLOCK_MISSILE : [(any_velocity, ItemSet(["M"]), any_pose)],
    AbstractTile.BLOCK_SUPER : [(any_velocity, ItemSet(["S"]), any_pose)],
    AbstractTile.BLOCK_POWER_BOMB : [(any_velocity, ItemSet(["MB", "PB"]), any_pose)],
    AbstractTile.BLOCK_GRAPPLE : [(any_velocity, ItemSet(["G"]), any_pose)],
    #TODO: speed can break bomb blocks
    AbstractTile.BLOCK_SPEED : [(speed_velocity_l, ItemSet(["SB"]), any_pose),
                                (speed_velocity_r, ItemSet(["SB"]), any_pose)],
    #TODO: can't actually treat /adjacent/ crumble blocks as air...
    # Positional requirements
    AbstractTile.BLOCK_CRUMBLE : [(crumble_velocity, ItemSet([]), any_pose)],
    AbstractTile.BLOCK_SHOT : [(any_velocity, ItemSet([]), any_pose)],
}

def meets(samus_state, requirement):
    v, i, p = requirement
    iv = samus_state.velocity in v
    ii = samus_state.items >= i
    ip = samus_state.pose in p
    return iv and ii and ip

def tile_is_air(samus_state, tile_type):
    if tile_type not in block_air_requirements:
        return False
    requirements = block_air_requirements[tile_type]
    for r in requirements:
        if meets(samus_state, r):
            return True
    return False

def tile_is_solid(samus_state, tile_type):
    if tile_type not in block_solid_requirements:
        return False
    requirements = block_solid_requirements[tile_type]
    if requirements == "Reciprocal":
        return not tile_is_air(samus_state, tile_type)
    for r in requirements:
        if meets(samus_state, r):
            return True
    return False

def tile_matches(samus_state, tile_type, as_what):
    assert as_what in [AbstractTile.SOLID, AbstractTile.AIR]
    if as_what == AbstractTile.SOLID:
        return tile_is_solid(samus_state, tile_type)
    else:
        return tile_is_air(samus_state, tile_type)

pose_hitboxes = {
    SamusPose.STAND: [Coord(0,0), Coord(0,1), Coord(0,2)],
    SamusPose.MORPH: [Coord(0,0)],
    SamusPose.JUMP: [Coord(0,0), Coord(0,1), Coord(0,2)],
    SamusPose.SPIN: [Coord(0,0), Coord(0,1)]
    }

def get_adj(pos, pose, direction):
    s_t = samus_tiles(pos, pose)
    h_t = [t + direction for t in s_t if t + direction not in s_t]
    return h_t

def get_horizontal_adj(s, scan_direction):
    h = Coord(scan_direction.x, 0)
    return get_adj(s, h)

def get_vertical_adj(s, scan_direction):
    v = Coord(0, scan_direction.y)
    return get_adj(s, v)

def get_all_adj(pos, pose):
    s_t = samus_tiles(pos, pose)
    l = []
    for t in s_t:
        ns = t.neighbors()
        for n in ns:
            if n not in s_t:
                l.append(n)
    return l

def check_collision(collide_tiles, new_origin, new_level, position):
    for b in collide_tiles:
        if new_level[b + position - new_origin] == AbstractTile.SOLID:
            return True
    return False

def samus_tiles(pos, pose):
    return [pos + t for t in pose_hitboxes[pose]]

def copy_items(items_list):
    return [(c.copy(), i.copy()) for c,i in self.items]

class LevelState(object):
    """
    Composable structure that keeps track of level data.
    """

    def __init__(self, origin, level, liquid_type, liquid_level, items):
        self.origin = origin
        self.level = level
        # Set the writeable false flag in order to allow hashing
        self.level.flags.writeable = False
        self.liquid_type = liquid_type
        self.liquid_level = liquid_level
        #TODO: does items need to be copied?
        # Items is Coord -> ItemSet
        self.items = items

    @property
    def shape(self):
        return Coord(self.level.shape[0], self.level.shape[1])

    @property
    def rect(self):
        return Rect(self.origin, self.origin + self.shape)

    def paste(self, level_origin, level):
        assert self.origin + self.shape <= Coord(level.shape[0], level.shape[1])
        o = self.origin - level_origin
        assert o >= Coord(0,0), o
        level[o.x:o.x + self.shape.x, o.y:o.y + self.shape.y] = self.level

    def copy(self):
        l = np.copy(self.level)
        return LevelState(self.origin.copy(), l, self.liquid_type, self.liquid_level, self.items)

    def __hash__(self):
        return hash((self.origin, bytes(self.level.data), self.liquid_type, self.liquid_level))

    def __eq__(self, other):
        o = self.origin == other.origin
        l = np.array_equal(self.level, other.level)
        s = self.shape == other.shape
        lt = self.liquid_type == other.liquid_type
        ll = self.liquid_level == other.liquid_level
        return o and l and s and lt and ll

    def __getitem__(self, index):
        internal_index = index - self.origin
        # Do not allow negative indexing
        if Coord(0,0) > internal_index:
            raise IndexError(internal_index)
        return self.level[internal_index]

    def in_bounds(self, index):
        try:
            t = self[index]
            return True
        except IndexError:
            return False

    def horizontal_flip(self):
        o = self.origin.copy()
        d = np.copy(self.level)
        d = np.flip(d, 0)
        #TODO: self.items must be flipped
        assert False
        return LevelState(o, d, self.liquid_type, self.liquid_level, self.items)

class SamusState(object):

    def __init__(self, position, velocity, items, pose):
        self.position = position
        self.velocity = velocity
        self.items = items
        self.pose = pose

    def __geq__(self, other):
        p = self.position == other.position
        v = self.velocity == other.velocity
        #TODO: what about negative speed?
        i = self.items >= other.items
        pose = self.pose is other.pose
        return p and v and i and pose

    def meets(self, other):
        v = self.velocity >= other.velocity
        i = self.items >= other.items
        pose = self.pose is other.pose
        return v and i and pose

    def copy(self):
        return SamusState(self.position.copy(),
                self.velocity.copy(), self.items.copy(), self.pose)

    def __hash__(self):
        return hash((self.position, self.velocity, self.items, self.pose))

    def __eq__(self, other):
        p = self.position == other.position
        v = self.velocity == other.velocity
        i = self.items == other.items
        pose = self.pose == other.pose
        return p and v and i and pose

    def horizontal_flip(self, level):
        position = self.position.flip_in_rect(level.rect, Coord(1, 0))
        v = self.velocity.horizontal_flip()
        i = self.items.copy()
        p = self.pose
        return SamusState(position, v, i, p)

    def collide(self, ds):
        print("collided")
        s = self.copy()
        v = self.velocity
        for d in ds:
            # Landing on the ground
            if d == Coord(0, 1):
                vh = HVelocity(VType.RUN, 0)
                vv = 0
                v = Velocity(vv, vh)
                s.velocity = v
                # Any non-morph pose leaves you standing
                #TODO: what if you're in spin in a 2-high gap -- this will clip you into the floor!!
                if s.pose != SamusPose.MORPH:
                    s.pose = SamusPose.STAND
            # Colliding with the ceiling
            elif d == Coord(0, -1):
                vv = 0
                v = Velocity(vv, s.velocity.vh.copy())
                s.velocity = v
            # Colliding with a wall (kill horizontal velocity)
            else:
                vh = HVelocity(VType.RUN, 0)
                v = Velocity(s.velocity.vv, vh)
                s.velocity = v
        print(s.position)
        print(s.velocity)
        return s
                
class SearchState(object):

    def __init__(self, samus, level):
        self.samus = samus
        self.level = level
    
    #TODO: water?
    def to_image(self):
        i = Image.new("RGB", (self.level.shape[0], self.level.shape[1]))
        pixels = i.load()
        # Set the pixels
        for xy in self.level.rect:
            pixel_xy = xy - self.level.origin
            pixels[pixel_xy] = abstract_to_color[self.level[xy]]
        return i

    def __hash__(self):
        return hash((self.samus, self.level))

    def __eq__(self, other):
        return self.samus == other.samus and self.level == other.level

    def copy(self):
        return SearchState(self.samus.copy(), self.level.copy())

    def horizontal_flip(self):
        samus = self.samus.horizontal_flip(self.level)
        level = self.level.horizontal_flip()
        return SearchState(samus, level)

class SamusFunction(object):
    def __init__(self, vfunction, required_items, gain_items, before_pose, after_pose, after_position):
        # before_position is always (0,0), after_position is relative
        self.vfunction = vfunction
        self.required_items = required_items
        self.gain_items = gain_items
        self.before_pose = before_pose
        self.after_pose = after_pose
        self.after_position = after_position

    def apply(self, samus_state, item_locations):
        # First, check if samus has the items to complete the rule
        if not samus_state.items >= self.required_items:
            return None, "Missing items"
        # Then, check that items that are picked up during the rule actually exist:
        items = samus_state.items.copy()
        for g in self.gain_items:
            rel_position = g + samus_state.position
            if rel_position not in item_locations:
                return None, "Required item does not exist"
            # Add the item picked up from that location
            items |= item_locations[rel_position]
        #print(samus_state.position, samus_state.pose)
        v = self.vfunction.apply(samus_state.velocity)
        if v is None:
            return None, "Velocity application failed"
        if not samus_state.pose == self.before_pose:
            return None, "Incorrect pose, in {} but needed {}".format(samus_state.pose, self.before_pose)
        else:
            pose = self.after_pose
        position = samus_state.position + self.after_position
        return SamusState(position, v, items, pose), None

    def horizontal_flip(self):
        vnew = self.vfunction.horizontal_flip()
        # Flip the after position horizontally too
        pnew = Coord(-self.after_position.x, self.after_position.y)
        # Flip the set of items obtained
        new_items = [Coord(-g.x, g.y) for g in self.gain_items]
        return SamusFunction(vnew, self.required_items, new_items, self.before_pose, self.after_pose, pnew)

    def compose(self, other):
        vnew = self.vfunction.compose(other.vfunction)
        if vnew is None:
            return None
        # Need the items for both
        r_i = self.required_items | other.required_items
        # Gain the items from both
        # Compute the new positions of the other items based on where other is applied relative to self
        #TODO: this is the "strict" version, where items that you pick up during a long rule
        # cannot be used later in the rule.
        # It is also possible to have a "loose" version, where composition picks an instantiation of the item
        # Then allows use of that item later, but then stores a constraint list for which instantiation was chosen
        # During application, both the positions of items and the explicit instantiation (if any) would be checked.
        # This roughly corresponds to the composition semantics for having a different rule for each item that would
        # be picked up.
        other_items_rel = [o + self.after_position for o in other.gain_items]
        g_i = self.gain_items + other_items_rel
        # Incompatible if the poses don't align
        if not self.after_pose == other.before_pose:
            return None
        else:
            b_p = self.before_pose
            a_p = other.after_pose
        pnew = self.after_position + other.after_position
        return SamusFunction(vnew, r_i, g_i, b_p, a_p, pnew)

class IntermediateState(object):
    def __init__(self, pos, walls, airs, function):
        self.pos = pos
        self.walls = walls
        self.airs = airs
        self.samusfunction = function

    def horizontal_flip(self):
        pos = Coord(-self.pos.x, self.pos.y)
        walls = [Coord(-w.x, w.y) for w in self.walls]
        airs = [(Coord(-d.x, d.y), [Coord(-t.x, t.y) for t in tiles]) for d, tiles in self.airs]
        if self.samusfunction is None:
            sf = None
        else:
            sf = self.samusfunction.horizontal_flip()
        return IntermediateState(pos, walls, airs, sf)

    def shift(self, pos):
        s = self.samus_state.copy()
        s += pos
        w = self.walls.copy()
        a = self.airs.copy()
        return IntermediateState(s,w,a,self.samusfunction)

def level_check_and_make(level, origin, tile, tile_type, samus_state):
    """Helper for LevelFunction apply()"""
    l = get_tile(level, origin, tile)
    if l is None:
        return None
    if l == AbstractTile.UNKNOWN:
        level[tile] = tile_type
        return "ok"
    # Don't need to overwrite if there's already a tile that matches
    if tile_matches(samus_state, l, tile_type):
        return "ok"
    else:
        return None

def level_check(level, origin, tile, tile_type, samus_state):
    l = get_tile(level, origin, tile)
    if l is None:
        return None
    if tile_matches(samus_state, l, tile_type):
        return True
    else:
        return False

def get_tile(level, origin, tile):
    index = tile - origin
    try:
        # Do not allow negative indexing
        if Coord(0,0) > index:
            return None
        return level[index]
    # Do not allow oob indexing
    except IndexError:
        return None

class LevelFunction(object):

    def __init__(self, liquid_type, liquid_interval, state_list):
        self.liquid_type = liquid_type
        self.liquid_interval = liquid_interval
        self.state_list = state_list

    def apply(self, state):
        # Convenience variables
        sl = state.level
        origin = sl.origin
        # Check liquid interval compatibility
        # Get absolute interval from relative
        l_i = self.liquid_interval.shift(state.samus.position.y)
        # Cannot apply if liquid does not match
        if state.level.liquid_level not in l_i:
            return None, "Liquid level does not match!"
        # If the liquidtype is none, that means that ANY liquidtype is acceptable
        # within the designated interval
        if self.liquid_type is not LiquidType.NONE and state.level.liquid_type != self.liquid_type:
            print(state.level.liquid_type)
            print(self.liquid_type)
            return None, "Liquid type does not match!"
        # Copy level state for editing
        level_array = np.copy(state.level.level)
        level_array.flags.writeable = True
        # Now envision each intermediate state sequentially
        intermediate_samus = state.samus.copy()
        for i_state in self.state_list:
            # Get the intermediate absolute samus state from relative
            # If it's a "key" state, use the built-in function to determine pose / velocity, etc.
            if i_state.samusfunction is not None:
                intermediate_samus, _ = i_state.samusfunction.apply(intermediate_samus, sl.items)
                assert intermediate_samus is not None
            intermediate_samus.position = i_state.pos + state.samus.position
            #print("pos:", intermediate_samus.position)
            #print("pose:", intermediate_samus.pose)
            #print("internal_pos:", i_state.pos)
            #print("walls", i_state.walls)
            #print("airs:", i_state.airs)
            # Check and create necessary airs
            for t in samus_tiles(intermediate_samus.position, intermediate_samus.pose):
                ok = level_check_and_make(level_array, origin, t, AbstractTile.AIR, intermediate_samus)
                # Could not reconcile air to the tiles samus occupies
                if ok is None:
                    return None, "Samus occupies solid tiles at {}".format(t)
            # Check and create necessary solids
            for rel_t in i_state.walls:
                g_t = rel_t + intermediate_samus.position
                ok = level_check_and_make(level_array, origin, g_t, AbstractTile.SOLID, intermediate_samus)
                # Could not reconcile solid to the tiles indicated as walls
                if ok is None:
                    return None, "Required wall not present at {}".format(g_t)
            # Check nearby airs for partial application
            conflict_ds = []
            for d, rel_ts in i_state.airs:
                conflict = False
                # Collect partial application conflicts
                for rel_t in rel_ts:
                    g_t = rel_t + intermediate_samus.position
                    # There's a conflict if a required tile can be reconciled to solid
                    if level_check(level_array, origin, g_t, AbstractTile.SOLID, intermediate_samus):
                        conflict = True
                if conflict:
                    conflict_ds.append(d)
            # If there was a conflict, partially apply the rule
            if len(conflict_ds) > 0:
                #print("Collision along {}".format(conflict_ds))
                samus = intermediate_samus.collide(conflict_ds)
                level = LevelState(sl.origin.copy(), level_array, sl.liquid_type, sl.liquid_level, sl.items)
                return SearchState(samus, level), None
        # No conflict
        # Create the new level state
        level = LevelState(sl.origin.copy(), level_array, sl.liquid_type, sl.liquid_level, sl.items)
        return SearchState(intermediate_samus, level), None

    def horizontal_flip(self):
        l = self.liquid_type
        i = self.liquid_interval.copy()
        sl = [state.horizontal_flip() for state in self.state_list]
        return LevelFunction(l, i, sl)

    def get_end_pos(self):
        state, _ = self.state_list[-1]
        return state.position

    def compose(self, other):
        # Check liquid type compatibility
        if self.liquid_type != other.liquid_type:
            return None
        new_lt = self.liquid_type
        # Other liquid level interval is relative to the ending position
        end_p = self.get_end_pos()
        rel_other_interval = other.liquid_interval.shift(end_p.y)
        new_li = self.liquid_interval.intersect(rel_other_interval)
        # Incompatible if they require disjoint liquid placements
        if new_li is None:
            return None
        # Check compatibility of states
        self_end = self.state_list[-1][0]
        other_start = other.state_list[0][0]
        #TODO:
        if not self_end >= other_start:
            return None
        # Update relative positions for the other rule
        #TODO: or store states relative to each other
        other_relstates = [state.shift(end_p) for state in other.state_list]
        new_state_list = self.state_list + other_relstates
        return LevelFunction(new_lt, new_li, new_state_list)

class StateFunction(object):

    def __init__(self, name, state_function, level_transition, cost):
        self.name = name
        self.state_function = state_function
        self.level_transition = level_transition
        self.cost = cost

    #TODO
    def apply(self, state):
        print("Applying Rule: {}".format(self.name))
        print(state.samus.position)
        print(state.samus.velocity)
        new_s, s_err = self.state_function.apply(state.samus, state.level.items)
        # Cannot be applied
        if new_s is None:
            return None, s_err
        # Applying the level transition accesses the entire state
        new_l, l_err = self.level_transition.apply(state)
        # Cannot be applied
        if new_l is None:
            return None, l_err
        # If it was applied, get the level information and the samus state from the
        # level information and the (possibly partially applied) level transition
        print("New:")
        print(new_l.samus.position)
        print(new_l.samus.velocity)
        return new_l, None

    def horizontal_flip(self):
        #TODO: do names even make sense? hf of hf is the same transition with a different name, for example...
        new_name = self.name + "_hf"
        new_sf = self.state_function.horizontal_flip()
        new_lt = self.level_transition.horizontal_flip()
        return StateFunction(new_name, new_sf, new_lt, self.cost)
    
    def compose(self, other):
        new_name = self.name + other.name
        new_sf = self.state_function.compose(other.state_function)
        new_lt = self.level_transition.compose(other.level_transition)
        #TODO Do the costs add? How to represent discounts?
        new_cost = self.cost + other.cost
        if new_sf is None or new_lt is None:
            return None
        else:
            return StateFunction(self, new_name, new_sf, new_lt, new_cost)

class Transition(object):

    def __init__(self, requirement, end_state):
        self.requirement = requirement
        self.end_state = end_state

    def horizontal_flip(self):
        r = self.requirement.horizontal_flip(self.end_state.level)
        e = self.end_state.horizontal_flip()
        return Transition(r, e)

class Rule(object):

    def __init__(self, name, transition_list, base_cost, extra_costs = None):
        #TODO: assert that each final state meets the requirements of the next state
        self.name = name
        self.transitions = transition_list
        self.base_cost = base_cost
        if extra_costs is None:
            self.extra_costs = []
        else:
            self.extra_costs = extra_costs

    def horizontal_flip(self):
        name = self.name + "_h"
        flipped_transitions = [t.horizontal_flip() for t in self.transitions]
        #TODO: how to structure the cost?
        base_cost = self.base_cost
        extra_costs = self.extra_costs.copy()
        return Rule(name, flipped_transitions, base_cost, extra_costs)

    @property
    def cost(self):
        return self.base_cost + sum(self.extra_costs)
    
    #TODO
    # Composes two Rules
    def __add__(self, other):
        before_state = self.before_state
        #TODO: recompute offset
        #TODO: check compatibility of self.after with other.before
        #TODO: compute levels
        #TODO: discounting scheme
        base_cost = self.base_cost + other.base_cost
        extra_costs = self.extra_costs + other.extra_costs
        return Rule(before_state, after_state, base_cost, extra_costs)

