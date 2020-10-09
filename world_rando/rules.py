from PIL import Image
import numpy as np
from enum import IntEnum
from sm_rando.world_rando.coord import Coord, Rect

class AbstractTile(IntEnum):
    UNKNOWN = 0
    AIR = 1
    SOLID = 2
    AIR_VERT_STOP = 3
    AIR_HORIZ_STOP = 4
    PLAN_SOLID = 5
    GRAPPLE = 6
    WATER = 7
    WATER_VERT_STOP = 8
    WATER_HORIZ_STOP = 9

abstract_to_color = {
    AbstractTile.UNKNOWN : (255, 255, 255),
    AbstractTile.AIR : (251, 242, 54),
    AbstractTile.SOLID : (0, 0, 0),
    AbstractTile.PLAN_SOLID : (255, 22, 169),
    AbstractTile.WATER : (48, 185, 211),
    AbstractTile.GRAPPLE : (119, 33, 105),
    }

def simplify(tile):
    if tile == AbstractTile.AIR_VERT_STOP:
        return AbstractTile.AIR
    elif tile == AbstractTile.AIR_HORIZ_STOP:
        return AbstractTile.AIR
    elif tile == AbstractTile.WATER_VERT_STOP:
        return AbstractTile.WATER
    elif tile == AbstractTile.WATER_HORIZ_STOP:
        return AbstractTile.WATER
    else:
        return tile

class SamusPose(IntEnum):
    STAND = 0
    MORPH = 1
    JUMP = 2
    SPIN = 3

class VType(IntEnum):
    # Special "untyped" zero velocity
    RUN = 1
    SPEED = 2
    WATER = 3

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

class VelocityFunction(object):

    def __init__(self, domain, vertical_b, horizontal_b, vadd):
        self.domain = domain
        self.vertical_behavior = vertical_b
        self.horizontal_behavior = horizontal_b
        self.vadd = vadd

    def __call__(self, velocity):
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
        return HVelocity(t, self.value + other.value)

    def flip(self):
        return HVelocity(self.type, -self.value)

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
        #TODO: what about min and max?
        v = self.vv + other.vv
        h = self.vh + other.vh
        assert h is not None
        return Velocity(v, h)

#TODO
pose_hitboxes = {
    SamusPose.STAND: [Coord(0,0), Coord(0,1), Coord(0,2)],
    SamusPose.MORPH: [Coord(0,0)],
    SamusPose.JUMP: [Coord(0,0), Coord(0,1), Coord(0,2)],
    SamusPose.SPIN: [Coord(0,0), Coord(0,1)]
    }

def apply_transition(before_state, transition):
    rule_before = transition.requirement
    rule_state = transition.end_state
    if not before_state.samus.meets(rule_before):
        return None, 0, "Samus does not meet rule prerequisites"
    # Determine the global location of frame2 using the local position of samus within frame2
    frame2_position = before_state.samus.position - rule_before.position
    #TODO: some way to know if the rule was partially applied
    new_state, n_changed, err = before_state.level.add(before_state, rule_state, frame2_position)
    # Can fail if the level additions contradict existing terrain
    if new_state is None:
        return None, 0, err
    return new_state, n_changed, ""

# Iterable over the relative states samus moves through to execute the rule
# x outer, y inner
def states_in_order(before_state, rule_state, scan_direction):
    assert rule_state.level.origin == Coord(0,0)
    for xy in rule_state.level.rect.iter_direction(scan_direction):
        # Only actual tiles should be copied
        if rule_state.level[xy] != AbstractTile.UNKNOWN:
            vertical_speed = rule_state.samus.position.y - xy.y
            # Copy horizontal speed and pose from the rule state
            sstate = rule_state.samus.copy()
            sstate.position = xy
            sstate.vertical_speed = vertical_speed
            s_t = samus_tiles(sstate)
            # If the tiles are not all air tiles, samus cannot fit
            # Determine if the rule puts samus at the given position
            samus_pass = True
            for s in s_t:
                if rule_state.level.in_bounds(s):
                    tile = rule_state.level[s]
                    # No air means that samus does not pass through this tile
                    if tile != AbstractTile.AIR:
                        samus_pass = False
                # Out of bounds means that samus does not pass through this tile
                else:
                    samus_pass = False
            if samus_pass:
                yield xy, sstate
            else:
                yield xy, None

def get_horizontal_adj(s, rule_state, scan_direction):
    h = Coord(scan_direction.x, 0)
    s_t = samus_tiles(s)
    h_tiles = [t + h for t in s_t]
    l = rule_state.level
    return [h for h in h_tiles if l.in_bounds(h) and l[h] == AbstractTile.AIR_HORIZ_STOP]

def get_vertical_adj(s, rule_state, scan_direction):
    v = Coord(0, scan_direction.y)
    s_t = samus_tiles(s)
    v_tiles = [t + v for t in s_t if t + v not in s_t]
    l = rule_state.level
    return [v for v in v_tiles if l.in_bounds(v) and l[v] == AbstractTile.AIR_VERT_STOP]

def check_collision(collide_tiles, new_origin, new_level, position):
    for b in collide_tiles:
        if new_level[b + position - new_origin] == AbstractTile.SOLID:
            return True
    return False

def samus_tiles(samus_state):
    return [samus_state.position + t for t in pose_hitboxes[samus_state.pose]]

#TODO: handle negative numbers!
def update(new_origin, new_level, before_state, rule_state, position):
    n_changed = 0
    # The global position of the ending state for samus
    s_new = position + rule_state.samus.position
    # The direction of samus' movement during the rule update
    scan_direction = (s_new - before_state.samus.position).sign()
    samus_state = before_state
    for tile, s in states_in_order(before_state, rule_state, scan_direction):
        # First, check the tile for conflicts and copy the tile
        global_tile = tile + position
        # The tile that will actually be written
        write_tile = simplify(rule_state.level[tile])
        # If the existing tile can be treated as a the required tile, replace it
        if new_level[global_tile - new_origin] == AbstractTile.UNKNOWN or new_level[global_tile - new_origin] == write_tile:
            if new_level[global_tile - new_origin] == AbstractTile.UNKNOWN:
                n_changed += 1
            new_level[global_tile - new_origin] = write_tile
        # Otherwise, there's a tile conflict
        else:
            #print("Tile conflict")
            return None, 0, "Tile conflict at {}".format(global_tile)
        # If samus travels through this square while executing the rule,
        # check for early stopping.
        if s is not None:
            global_s = s.copy()
            s.position += position
            # Get the horizontally relevant squares
            # A square is relevant if it is horizontally adjacent to the
            # state and is not blank in the rule
            # Relevant squares must be checked for collisions for early failure
            h = get_horizontal_adj(s, rule_state, scan_direction)
            # Get the vertically relevant squares
            v = get_vertical_adj(s, rule_state, scan_direction)
            h_collide = check_collision(h, new_origin, new_level, position)
            v_collide = check_collision(v, new_origin, new_level, position)
            # Abort early if samus collides with something
            #TODO: order of collision matters / both collision?
            if h_collide:
                #print("Horizontal Collision")
                global_s.horizontal_speed = 0
                return global_s, n_changed, ""
            elif v_collide:
                #print("Vertical Collision")
                global_s.vertical_speed = 0
                return global_s, n_changed, ""
    end_state = rule_state.samus.copy()
    end_state.position += position
    return end_state, n_changed, ""

#TODO: Reverse function to create rules traveling from right to left
#TODO: remove size (is kept as part of the level data array
class LevelState(object):
    """
    Composable structure that keeps track of level data.
    """

    def __init__(self, origin, level, max_size=None):
        self.origin = origin
        self.level = level
        # Set the writeable false flag in order to make hashing possible
        self.level.flags.writeable = False
        self.max_size = max_size

    @property
    def size(self):
        return Coord(self.level.shape[0], self.level.shape[1])

    @property
    def rect(self):
        return Rect(self.origin, self.origin + self.size)

    def add(self, before_state, rule_state, position):
        other = rule_state.level
        # Vector pointing to the new origin from the old origin
        new_origin = self.origin.pointwise_min(position)
        new_rect = self.rect.containing_rect(other.rect.translate(position))
        # Size points past the bottom right corner
        self_end = self.origin + self.size
        other_end = position + other.size
        # The size of the new frame
        new_size = new_rect.size_coord()
        if self.max_size is None:
            new_max_size = other.max_size
        elif other.max_size is None:
            new_max_size = self.max_size
        else:
            new_max_size = self.max_size.pointwise_min(other.max_size)
        assert new_max_size is None or new_size <= new_max_size
        # Allocate the new frame filled with blank tiles
        new_level_data = np.zeros(new_size, dtype="int")
        self.paste(new_origin, new_level_data)
        sstate, n_changed, err = update(new_origin, new_level_data, before_state, rule_state, position)
        if sstate is None:
            return None, 0, err
        lstate = LevelState(new_origin, new_level_data, new_max_size)
        return SearchState(sstate, lstate), n_changed, ""

    def paste(self, level_origin, level):
        assert self.origin + self.size <= Coord(level.shape[0], level.shape[1])
        o = self.origin - level_origin
        assert o >= Coord(0,0), o
        level[o.x:o.x + self.size.x, o.y:o.y + self.size.y] = self.level

    def copy(self):
        l = np.copy(self.level)
        if self.max_size is None:
            m = None
        else:
            m = self.max_size.copy()
        return LevelState(self.origin.copy(), l, m)

    def __hash__(self):
        return hash((self.origin, bytes(self.level.data), self.max_size))

    def __eq__(self, other):
        o = self.origin == other.origin
        l = np.array_equal(self.level, other.level)
        s = self.size == other.size
        m = self.max_size == other.max_size
        return o and l and s and m

    def __getitem__(self, index):
        internal_index = index - self.origin
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
        if self.max_size is None:
            m = None
        else:
            m = self.max_size.copy()
        return LevelState(o, d, m)

class SamusState(object):

    def __init__(self, position, vertical_speed, horizontal_speed, items, pose):
        self.position = position
        self.vertical_speed = vertical_speed
        self.horizontal_speed = horizontal_speed
        self.items = items
        self.pose = pose

    def __geq__(self, other):
        p = self.position == other.position
        vv = self.vertical_speed == other.vertical_speed
        #TODO: what about negative speed?
        vh = self.horizontal_speed >= other.horizontal_speed
        i = self.items >= other.items
        pose = self.pose is other.pose
        return p and vv and vh and i and pose

    def meets(self, other):
        vv = self.vertical_speed == other.vertical_speed
        vh = self.horizontal_speed >= other.horizontal_speed
        i = self.items >= other.items
        pose = self.pose is other.pose
        return vv and vh and i and pose

    def copy(self):
        return SamusState(self.position.copy(),
                self.vertical_speed, self.horizontal_speed, self.items.copy(), self.pose)

    def __hash__(self):
        return hash((self.position, self.vertical_speed, self.horizontal_speed, self.items, self.pose))

    def __eq__(self, other):
        p = self.position == other.position
        v = self.vertical_speed == other.vertical_speed
        h = self.horizontal_speed == other.horizontal_speed
        i = self.items == other.items
        pose = self.pose is other.pose
        return p and v and h and i and pose

    def horizontal_flip(self, level):
        position = self.position.flip_in_rect(level.rect, Coord(1, 0))
        v = self.vertical_speed
        h = -self.horizontal_speed
        i = self.items.copy()
        p = self.pose
        return SamusState(position, v, h, i, p)

class SearchState(object):

    def __init__(self, samus, level):
        self.samus = samus
        self.level = level

    # Apply a rule to reach a new search state
    def apply_rule(self, rule):
        print("Considering: {}".format(rule.name))
        current_state = self
        n_changed = 0
        for transition in rule.transitions:
            result = apply_transition(current_state, transition)
            if result is None:
                return None, 0, err
            current_state, n, err = result
            n_changed += n
        return current_state, n_changed, err

    def to_image(self):
        i = Image.new("RGB", (self.level.size.x, self.level.size.y))
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

    def apply(self, samus_state):
        v = self.vfunction.apply(samus_state.velocity)
        if v is None:
            return None
        if not samus_state.items >= self.required_items:
            return None
        else:
            items |= self.gain_items
        if not samus_state.pose == self.before_pose:
            return None
        else:
            pose = self.after_pose
        position = samus_state.position + self.after_position
        return SamusState(position, v, items, pose)

    def horizontal_flip(self):
        vnew = self.vfunction.horizontal_flip()
        pnew = self.after_position.horizontal_flip()
        return SamusFunction(vnew, self.required_items, self.gain_items, self.before_pose, self.after_pose, pnew)

    def compose(self, other):
        vnew = self.vfunction.compose(other.vfunction)
        if vnew is None:
            return None
        # Need the items for both
        r_i = self.required_items | other.required_items
        # Gain the items from both
        g_i = self.gain_items | other.gain_items
        # Incompatible if the poses don't align
        if not self.after_pose == other.before_pose:
            return None
        else:
            b_p = self.before_pose
            a_p = other.after_pose
        pnew = self.after_position + other.after_position
        return SamusFunction(vnew, r_i, g_i, b_p, a_p, pnew)

class IntermediateState(object):
    def __init__(self, samus_state, walls, airs):
        self.samus = samus_state
        self.walls = walls
        self.airs = airs

    def horizontal_flip(self):
        p = Coord(-self.samus.pos.x, self.samus.pos.y)
        samus = self.samus.copy()
        samus.pos = p
        walls = [Coord(-w.x, w.y) for w in self.walls]
        airs = [(Coord(-d.x, d.y), [Coord(-t.x, t.y) for t in tiles]) for d, tiles in self.airs]
        return IntermediateState(samus, walls, airs)

    def shift(self, pos):
        s = self.samus_state.copy()
        s += pos
        w = self.walls.copy()
        a = self.airs.copy()
        return IntermediateState(s,w,a)

class LevelFunction(object):

    def __init__(self, liquid_type, liquid_interval, state_list):
        self.liquid_type = liquid_type
        self.liquid_interval = liquid_interval
        self.state_list = state_list

    def apply(self, state):
        #check liquid interval compatibility
        # Get absolute interval from relative
        l_i = self.liquid_interval.shift(state.samus.pos)
        # Cannot apply if liquid does not match
        if state.level.liquid_level not in l_i:
            return None
        if state.level.liquid_type != self.liquid_type:
            return None
        # Copy level state for editing
        level = state.level.copy()
        # Now envision each intermediate state sequentially
        for i_state in self.state_list:
            # Get the intermediate absolute samus state from relative
            intermediate_samus = i_state.samus + state.samus.pos
            # Check and create necessary airs
            for t in samus_tiles(intermediate_samus):
                ok = level.check_and_make(t, AbstractTile.AIR, intermediate_samus)
                # Could not reconcile air to the tiles samus occupies
                if ok is None:
                    return None
            # Check and create necessary solids
            for rel_t in i_state.walls:
                g_t = rel_t + i_state.samus.pos
                ok = level.check_and_make(g_t, AbstractTile.SOLID, intermediate_samus)
                # Could not reconcile solid to the tiles indicated as walls
                if ok is None:
                    return None
            # Check nearby airs for partial application
            conflict_ds = []
            for d, rel_ts in i_state.airs:
                conflict = False
                # Collect partial application conflicts
                for rel_t in rel_ts:
                    g_t = rel_t + i_state.samus.pos
                    # There's a conflict if a required tile can be reconciled to solid
                    if level.check(g_t, AbstractTile.SOLID, intermediate_samus):
                        conflict = True
                if conflict:
                    conflict_ds.append(d)
            # If there was a conflict, partially apply the rule
            if len(conflict_ds) > 0:
                samus = collide(intermediate_samus, ds)
                return SearchState(intermediate_samus, ds)
        # No conflict
        return SearchState(intermediate_samus, level)

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
        self.state_function = state_function
        self.level_transition = level_transition
        self.cost = cost

    #TODO
    def apply(state):
        new_s = self.state_function.apply(state.samus)
        new_l = self.level_transition.apply(state.level)
        # Cannot be applied
        if new_s is None or new_l is None:
            return None
        # If it was applied, get the level information and the samus state from the
        # level information and the (possibly partially applied) level transition
        return new_l

    def horizontal_flip(self):
        #TODO: do names even make sense? hf of hf is the same transition with a different name, for example...
        new_name = self.name + "_hf"
        new_sf = self.state_function.horizontal_flip()
        new_lt = self.level_transition.horizontal_flip()
        return StateFunction(self, new_name, new_sf, new_lt, self.cost)
    
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

