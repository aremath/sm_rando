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
    if tile is AbstractTile.AIR_VERT_STOP:
        return AbstractTile.AIR
    elif tile is AbstractTile.AIR_HORIZ_STOP:
        return AbstractTile.AIR
    elif tile is AbstractTile.WATER_VERT_STOP:
        return AbstractTile.WATER
    elif tile is AbstractTile.WATER_HORIZ_STOP:
        return AbstractTile.WATER
    else:
        return tile

class SamusPose(IntEnum):
    STAND = 0
    MORPH = 1
    JUMP = 2
    SPIN = 3

#TODO
pose_hitboxes = {
    SamusPose.STAND: [Coord(0,0), Coord(0,1), Coord(0,2)],
    SamusPose.MORPH: [Coord(0,0)],
    SamusPose.JUMP: [Coord(0,0), Coord(0,1), Coord(0,2)],
    SamusPose.SPIN: [Coord(0,0), Coord(0,1)]
    }

def apply_rule(before_state, rule_before, rule_state):
    if not before_state.samus.meets(rule_before):
        return None
    # Determine the global location of frame2 using the local position of samus within frame2
    frame2_position = before_state.samus.position - rule_before.position
    #TODO: some way to know if the rule was partially applied
    new_state, n_changed = before_state.level.add(before_state, rule_state, frame2_position)
    # Can fail if the level additions contradict existing terrain
    if new_state is None:
        return None, 0
    return new_state, n_changed

# Iterable over the relative states samus moves through to execute the rule
# x outer, y inner
def states_in_order(before_state, rule_state, scan_direction):
    assert rule_state.level.origin == Coord(0,0)
    for xy in rule_state.level.rect.iter_direction(scan_direction):
        # Only actual tiles should be copied
        if xy is not AbstractTile.UNKNOWN:
            vertical_speed = rule_state.samus.position.y - xy.y
            # Copy horizontal speed and pose from the rule state
            sstate = rule_state.samus.copy()
            sstate.position = xy
            sstate.vertical_speed = vertical_speed
            s_t = samus_tiles(sstate)
            # If the tiles are not all air tiles, samus cannot fit
            # Determine if the rule puts samus at the given position
            for s in s_t:
                if rule_state.level.in_bounds(s):
                    tile = rule_state.level[s]
                    # No air means that samus does not pass through this tile
                    if tile is not AbstractTile.AIR:
                        yield xy, None
                # Out of bounds means that samus does not pass through this tile
                else:
                    yield xy, None
            yield xy, sstate

def get_horizontal_adj(s, rule_state, scan_direction):
    h = Coord(scan_direction.x, 0)
    s_t = samus_tiles(s)
    h_tiles = [t + h for t in s_t]
    l = rule_state.level
    return [h for h in h_tiles if l.in_bounds(h) and l[h] is AbstractTile.AIR_HORIZ_STOP]

def get_vertical_adj(s, rule_state, scan_direction):
    v = Coord(0, scan_direction.y)
    s_t = samus_tiles(s)
    v_tiles = [t + v for t in s_t if t + v not in s_t]
    l = rule_state.level
    return [v for v in v_tiles if l.in_bounds(v) and l[v] is AbstractTile.AIR_VERT_STOP]

def check_collision(collide_tiles, new_level, position):
    for b in collide_tiles:
        if new_level[b + position] is AbstractTile.SOLID:
            return True
    return False

def samus_tiles(samus_state):
    return [samus_state.position + t for t in pose_hitboxes[samus_state.pose]]

def update(new_level, before_state, rule_state, position):
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
        if new_level[tile] is AbstractTile.UNKNOWN or new_level[tile] == write_tile:
            if new_level[tile] is AbstractTile.UNKNOWN:
                n_changed += 1
            new_level[tile] = write_tile
        # Otherwise, there's a tile conflict
        else:
            return None, 0
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
            h_collide = check_collision(h, new_level, position)
            v_collide = check_collision(v, new_level, position)
            # Abort early if samus collides with something
            if h_collide or v_collide:
                l = LevelState()
            if h_collide:
                global_s.horizontal_speed = 0
                return global_s, n_changed
            elif v_collide:
                global_s.vertical_speed = 0
                return global_s, n_changed
    return rule_state, n_changed

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
        return Rect(self.origin, self.size)

    def add(self, before_state, rule_state, position):
        other = rule_state.level
        # Vector pointing to the new origin from the old origin
        new_origin = min(self.origin, position) # pointwise
        new_rect = self.rect.containing_rect(other.rect)
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
        new_level_data = np.zeros(new_size)
        self.paste(new_level_data)
        sstate, n_changed = update(new_level_data, before_state, rule_state, position)
        if sstate is None:
            return None, 0
        lstate = LevelState(new_origin, new_level_data, new_max_size)
        return SearchState(sstate, lstate), n_changed

    def paste(self, level):
        assert self.origin + self.size <= Coord(level.shape[0], level.shape[1])
        level[self.origin.x:self.origin.x + self.size.x, self.origin.y:self.origin.y + self.size.y] = self.level

    def copy(self):
        l = np.copy(self.level)
        if self.max_size is None:
            m = None
        else:
            m = self.max_size.copy()
        return LevelState(self.origin.copy(), l, m)

    def __hash__(self):
        return hash((self.origin, self.level, self.size, self.max_size))

    def __eq__(self, other):
        o = self.origin == other.origin
        l = np.array_equal(self.level, other.level)
        s = self.size == other.size
        m = self.max_size == other.max_size
        return o and l and s and m

    def __getitem__(self, index):
        return self.level[index]

    def in_bounds(self, index):
        try:
            t = self[index]
            return True
        except IndexError:
            return False

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

    def __eq__(self):
        p = self.position == other.position
        v = self.vertical_speed == other.vertical_speed
        h = self.horizontal_speed == other.horizontal_speed
        i = self.items == other.items
        pose = self.pose is other.pose
        return p and v and h and i and pose

#TODO: not necessary?
class Requirement(object):
    def __init__(self, vertical_speed, horizontal_speed, items):
        self.vertical_speed = vertical_speed
        self.horizontal_speed = horizontal_speed
        self.items = items

class SearchState(object):

    def __init__(self, samus, level):
        self.samus = samus
        self.level = level

    # Apply a rule to reach a new search state
    def apply_rule(self, rule):
        current_state = self
        n_changed = 0
        for req, rule_state in rule.transitions:
            result = apply_rule(current_state, req, rule_state)
            if result is None:
                return None
            current_state, n = result
            n_changed += n
        return current_state, n_changed

    def to_image(self):
        levelsimple = self.level.simplify()
        i = Image.new("RGB", (self.level.size.x, self.level.size.y))
        pixels = i.load()
        # Set the pixels
        for xy in Rect(Coord(0,0), self.level.size):
            pixels[xy.x, xy.y] = abstract_to_color[levelsimple.level[xy.x, xy.y]]
        return i

    def __hash__(self):
        return hash((self.samus, self.level))

    def __eq__(self, other):
        return self.samus == other.samus and self.level == other.level

    def copy(self):
        return SearchState(self.samus.copy(), self.level.copy())

class Rule(object):

    def __init__(self, name, requirements, rule_state, base_cost, extra_costs = None):
        #TODO: assert that each final state meets the requirements of the next state
        self.name = name
        self.transitions = [(requirements, rule_state)]
        self.base_cost = base_cost
        if extra_costs is None:
            self.extra_costs = []
        else:
            self.extra_costs = extra_costs

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

