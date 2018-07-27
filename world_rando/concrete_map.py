# Creates a concrete map based on an abstract map
# a map is a data structure:
# key1 - area (ex. "Maridia")
# key2 - (x,y) tuple
# value - MapTile
import collections
import heapq
import random
from enum import Enum

class MCoords(object):
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return MCoords(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return MCoords(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return MCoords(self.x * other.x, self.y * other.y)

    def up(self):
        return MCoords(self.x, self.y - 1)

    def right(self):
        return MCoords(self.x + 1, self.y)

    def down(self):
        return MCoords(self.x, self.y + 1)

    def left(self):
        return MCoords(self.x - 1, self.y)

    def neighbors(self):
        return self.left(), self.up(), self.right(), self.down()

    def to_tuple(self):
        return (self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash(self.to_tuple())

    def euclidean(self, other):
        return ((self.x-other.x)**2 + (self.y-other.y)**2)**(0.5)

    def __repr__(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"

    # stupid way to break priority ties
    def __lt__(self, other):
        return self.x + self.y < other.x + other.y

    def scale(self, scale_factor):
        return MCoords(scale_factor*self.x, scale_factor*self.y)

    def to_unit(self):
        magnitude = self.euclidean(MCoords(0,0))
        return self.scale(1/magnitude)

    def resolve_int(self):
        return MCoords(int(self.x), int(self.y))

    def wall_relate(self, other):
        if other == self.up():
            return "U"
        elif other == self.left():
            return "L"
        elif other == self.right():
            return "R"
        elif other == self.down():
            return "D"
        else:
            assert False, "No wall_relate"

    def in_bounds(self, lower, upper):
        """Is this MCoords inside the rectangle described by lower, upper?
        Like range, this includes the lower bound but not the upper bound. """
        return (self.x >= lower.x) and (self.y >= lower.y) and (self.x < upper.x) and (self.y < upper.y)

    def truncate(self, lower, upper):
        """Returns the tile inside the (lower,upper) rectangle closest to
        self."""
        new_x = self.x
        new_y = self.y
        if self.x < lower.x:
            new_x = lower.x
        elif self.x >= upper.x:
            new_x = upper.x - 1
        if self.y < lower.y:
            new_y = lower.y
        elif self.y >= upper.y:
            new_y = upper.y - 1
        return MCoords(new_x, new_y)

# Enum for what things a tile can be
class TileType(Enum):
    normal = 1         # Tile with some data - its image will be controlled by what walls it has
    blank = 2          # Blank tiles that are still stored in the map (ex. introduced by elevators.)
    up_arrow = 3       # The arrow above an elevator.
    down_arrow = 4         #
    elevator_shaft = 5     #
    elevator_main_up = 6   #
    elevator_main_down = 7 #

class MapTile(object):

    def __init__(self, _tile_type=TileType.normal, _fixed=False, _item=False, _save=False, _walls=None):
        # key - MCoords
        # value - itemset needed to reach
        self.d = collections.defaultdict(list)
        # set of ("L", "R", "U", "D") indicating which walls this tile has.
        if _walls is None:
            self.walls = set()
        else:
            self.walls = _walls
        # general tile info
        self.is_item  = _item
        self.is_save  = _save
        # elevator information
        self.tile_type = _tile_type
        # is it part of an already-constrained room?
        self.is_fixed = _fixed

    def add_path(to_coords, with_items):
        self.d[to_coords].append(with_items)

# Various distance metrics for use as search heuristics
def euclidean(p1, p2):
    """euclidean metric"""
    return p1.euclidean(p2)

def manhattan(p1, p2):
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)

# 9 chosen arbitrarily.
#TODO: scale factor is a random multiple of the euclidean distance?
# this tends to be more wiggly near the endpoint, and asymptotically straight
# near the starting point.
def rand_d(p1, p2):
    return euclidean(p1, p2) + random.uniform(0,9)

# Stores the information for a concrete map: What tiles are where.
# Provides search abilities, etc.
class ConcreteMap(object):
   
    # Avoid the infamous default value bug!
    def __init__(self, _dimensions, _tiles=None):
        # X, Y. The size of the ConcreteMap.
        # MCoords in the cmap should be between (0,0) and _dimensions
        self.dimensions = _dimensions
        # MCoords -> Maptile dictionary.
        if _tiles == None:
            self.tiles = {}
        else:
            self.tiles = _tiles

    def in_bounds(self, mcoord):
        return mcoord.in_bounds(MCoords(0,0), self.dimensions)
        
    def assert_in_bounds(self, mcoord):
        assert self.in_bounds(mcoord), "Out of bounds: " + str(mcoord)

    def map_extent(self):
        """ The extent of the cmap, two MCoords which specify the bounding box."""
        mtiles = self.keys()
        if len(mtiles) == 0:
            return None
        minx = min(mtiles, key=lambda item: item.x).x
        miny = min(mtiles, key=lambda item: item.y).y
        maxx = max(mtiles, key=lambda item: item.x).x
        maxy = max(mtiles, key=lambda item: item.y).y
        return (MCoords(minx, miny), MCoords(maxx, maxy))

    def map_range(self):
        """Returns the actual ranges of the map, along with the placement of that range in x,y"""
        mmin, mmax = self.map_extent()
        return mmax - mmin, mmin

    def at_offset(self, offset):
        """Returns a new cmap which is the old cmap with all tiles
        at an offset. Data may be shared."""
        new_tiles = {m + offset : mtile for m, mtile in self.items() }
        #TODO: and has the same dimensions as before?
        return ConcreteMap(self.dimensions, _tiles=new_tiles)

    def compose(self, other, collision_policy="error"):
        """Returns a new cmap which is a composition of self and other.
        If self and other share a maptile, then the collision policy decides."""
        new_tiles = {}
        for c, t in self.items():
            new_tiles[c] = t
        for c, t in other.items():
            self.assert_in_bounds(c)
            if c in new_tiles:
                # 'defer' means tiles from self are preferred over tiles from other
                if collision_policy == "defer":
                    continue
                # 'error' means bomb out when there's a conflict
                elif collision_policy == "error":
                    assert False, "Collision in compose: " + str(c)
                # 'none' means to not produce a composed cmap if there is a conflict
                elif collision_policy == "none":
                    return None
                else:
                    assert False, "Bad collision policy: " + collision_policy
            else:
                new_tiles[c] = t
        #TODO: which dimensions does it get?
        return ConcreteMap(self.dimensions, _tiles=new_tiles)

    #TODO: some optimizations can be made
    # note that dist can be random, in which case this is kind of a random walk that
    # 'eventually' reaches q
    def map_search(self, start, goal, reach_pred=lambda x: True, dist=lambda x,y: euclidean(x,y)):
        """search to find the path from start to goal, under tiles satisfying pred
        placing new tiles into the queue by sorting them over the metric dist. Does not
        search tiles outside the bounds of the ConcreteMap, ensuring the search space is finite. """
        self.assert_in_bounds(start)
        self.assert_in_bounds(goal)
        h = []
        finished = set()
        offers = {}
        heapq.heappush(h, (0, start))
        finished.add(start)
        while len(h) > 0:
            _, pos = heapq.heappop(h)
            if pos == goal:
                return offers, finished
            for a in pos.neighbors():
                if self.in_bounds(a) and a not in finished and reach_pred(a):
                    heapq.heappush(h, (dist(a, goal), a))
                    finished.add(a)
                    offers[a] = pos
        # not found
        return None

    def map_bfs(self, start, goal_pred, reach_pred=lambda x: True):
        """bfs over nodes satisfying reach_pred. If goal_pred is None, just returns all there was to see.
        If goal_pred is not none, searches for a node satisfying goal_pred."""
        self.assert_in_bounds(start)
        q = collections.deque([start])
        finished = set()
        offers = {}
        finished.add(start)
        while len(q) > 0:
            pos = q.popleft()
            if goal_pred is not None and goal_pred(pos):
                return pos, offers, finished
            n = pos.neighbors()
            for a in n:
                if self.in_bounds(a) and a not in finished and reach_pred(a):
                    q.append(a)
                    finished.add(a)
                    offers[a] = pos
        return None, offers, finished

    def elide_walls(self):
        """ adds walls to cmap where the tile abuts empty space """
        for xy in self.keys():
            n = xy.neighbors()
            for a in n:
                if a not in self:
                    self[xy].walls.add(xy.wall_relate(a))

    def random_rooms(self, n):
        # choose means
        means = random.sample(self.keys(), n)
        paths, partitions = bfs_partition(set(self.keys()), means)
        for mean in means:
            self.room_walls(partitions[mean])
        return paths, partitions

    def room_walls(self, room):
        """ puts the walls into a room, given as a set of MCoords """
        for xy in room:
            for n in xy.neighbors():
                if n not in room:
                    self[xy].walls.add(xy.wall_relate(n))

    def bounded_put(self, pos, mtile):
        """Puts mtile at pos if pos is in bounds, returns whether it succeeded."""
        if self.in_bounds(pos):
            self[pos] = mtile
            return True
        else:
            return False

    # Behaves like a dictionary, interfacing to tiles
    def __getitem__(self, key):
        return self.tiles[key]
    # Cannot set an item outside the bounds
    def __setitem__(self, key, value):
        if key.in_bounds(MCoords(0,0), self.dimensions):
            self.tiles[key] = value
        else:
            assert False, "Index not in bounds: " + str(key)
    def __len__(self):
        return len(self.tiles)
    def __contains__(self,item):
        return item in self.tiles
    def keys(self):
        return self.tiles.keys()
    def items(self):
        return self.tiles.items()
    def values(self):
        return self.tiles.values()

#TODO
def map_lsearch(start, goal, pred=lambda x:True, dist=lambda x,y: euclidean(x,y)):
    """special search that first finds failure states in moving from start to goal,
    then moves only towards the goal to reach it, minimizing dist at each step.
    The goal here is that we can generate random, but more 'straight' paths than a random
    walk will do."""
    diff = goal - start
    pass

def get_path(offers, start, end):
    if end not in offers:
        return None
    pos = end
    path = []
    while True:
        path.append(pos)
        if pos == start:
            break
        pos = offers[pos]
    return path[::-1]

#lambda x: 0 means BFS in a heapq (first element first)
# can use random to alter the pattern of vertices grabbed by
# each mean
def bfs_partition(space, means, priority=lambda x: 0):
    # setup
    # key - mean, value - set of positions that mean has considered
    mfinished = {mean: set() for mean in means}
    # key - mean, value - for position p, what made the a* offer to p?
    moffers = {mean: {} for mean in means}
    for mean in means:
        mfinished[mean].add(mean)
    mpos = {mean: mean for mean in means}
    mheaps = {mean: [(0, mean)] for mean in means}
    all_finished = set(means)
    while all_finished != space:
        for mean in means:
            if len(mheaps[mean]) > 0:
                _, mpos[mean] = heapq.heappop(mheaps[mean])
            else:
                continue
            for n in mpos[mean].neighbors():
                if n not in all_finished and n in space:
                    heapq.heappush(mheaps[mean], (priority(n), n))
                    mfinished[mean].add(n)
                    all_finished.add(n)
                    moffers[mean][n] = mpos[mean]
    return moffers, mfinished

###
# SPECIFY MAP TILES
# ways to specify a set of map tiles to search with map_search (using pred)
###

def is_above(xy1, xy2):
    return xy1.x == xy2.x and xy1.y < xy2.y

def is_below(xy1, xy2):
    return xy1.x == xy2.x and xy1.y > xy2.y

#TODO: with fold or any...
def is_p_list(xy1, xys, p):
    """does xy1 satisfy p with any element of xys?"""
    for xy2 in xys:
        if p(xy1, xy2):
            return True
    return False

def is_below_l(xy1, xys):
    return is_p_list(xy1, xys, is_below)

def is_above_l(xy1, xys):
    return is_p_list(xy1, xys, is_above)

