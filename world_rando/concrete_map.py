# Data types for concrete map creation
import collections
import heapq
import random
from enum import Enum
from .coord import Coord, Rect

# Enum for what things a tile can be
class TileType(Enum):
    """
    Encodes the type of a map tile
    Used for drawing the concrete map and for putting the concrete map into the game RAM
    """
    normal = 1         # Tile with some data - its image will be controlled by what walls it has
    blank = 2          # Blank tiles that are still stored in the map (ex. introduced by elevators.)
    up_arrow = 3       # The arrow above an elevator.
    down_arrow = 4         #
    elevator_shaft = 5     #
    elevator_main_up = 6   #
    elevator_main_down = 7 #

class MapTile(object):
    """
    Object that represents a single map tile. The entire map is populated with MapTiles
    """

    def __init__(self, _tile_type=TileType.normal, _fixed=False, _item=False, _save=False, _walls=None):
        # key - Coord
        # value - itemset needed to reach
        self.d = collections.defaultdict(list)
        # set of ("L", "R", "U", "D") indicating which walls this tile has.
        if _walls is None:
            self.walls = set()
        else:
            self.walls = _walls
        # general tile info
        self.is_item = _item
        self.is_save = _save
        # elevator information
        self.tile_type = _tile_type
        # is it part of an already-constrained room?
        self.is_fixed = _fixed

    def add_path(self, to_coords, with_items):
        """Add a path through self to another tile, with the specified item constraints"""
        self.d[to_coords].append(with_items)

# Various distance metrics for use as search heuristics
def euclidean(p1, p2):
    """Euclidean Metric"""
    return p1.euclidean(p2)

def manhattan(p1, p2):
    """Manhattan Metric"""
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)

# 9 chosen arbitrarily.
#TODO: scale factor is a random multiple of the euclidean distance?
# this tends to be more wiggly near the endpoint, and asymptotically straight
# near the starting point.
def rand_d(p1, p2):
    """Randomized Euclidean distance"""
    return euclidean(p1, p2) + random.uniform(0, 9)

class ConcreteMap(object):
    """
    Stores the information for a concrete map: What tiles are where.
    Provides search abilities, etc.
    """

    # Avoid the infamous default value bug!
    def __init__(self, _dimensions, _tiles=None):
        # X, Y. The size of the ConcreteMap.
        # Coord in the cmap should be between (0,0) and _dimensions
        self.dimensions = _dimensions
        # Coord -> Maptile dictionary.
        if _tiles is None:
            self.tiles = {}
        else:
            self.tiles = _tiles

    def in_bounds(self, coord):
        """Is the given coord in bounds?"""
        return coord.in_bounds(Coord(0, 0), self.dimensions)

    def assert_in_bounds(self, coord):
        """Assert that the given coordinate is in bounds"""
        assert self.in_bounds(coord), "Out of bounds: " + str(coord)

    def map_extent(self):
        """ The extent of the cmap, two Coord which specify the bounding box."""
        return extent(self.keys())

    def at_offset(self, offset):
        """Returns a new cmap which is the old cmap with all tiles
        at an offset. Data may be shared."""
        new_tiles = {m + offset : mtile for m, mtile in self.items()}
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
    def map_search(self, start, goal, reach_pred=lambda x: True, dist=euclidean):
        """search to find the path from start to goal, under tiles satisfying pred
        placing new tiles into the queue by sorting them over the metric dist. Does not
        search tiles outside the bounds of the ConcreteMap, ensuring the search space is finite. """
        self.assert_in_bounds(start)
        self.assert_in_bounds(goal)
        h = []
        finished = set([start])
        offers = {start: start}
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
        finished = set([start])
        offers = {start: start}
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

    def non_fixed(self):
        """Return the set of coordinates for non-fixed tiles."""
        return set(filter(lambda p: not self.tiles[p].is_fixed, self.keys()))

    def elide_walls(self):
        """Adds walls to cmap where the tile abuts empty space."""
        for xy in self.keys():
            n = xy.neighbors()
            for a in n:
                if a not in self:
                    self[xy].walls.add(xy.wall_relate(a))

    #TODO: the space is only the non-fixed tiles!
    # figure out why that hangs by printing the remaining tiles of set?
    # might need to create an initial condition of fixed rooms?
    #TODO: currently this alg assumes that the non-fixed rooms are connected.
    # This assumption can be broken with Mother Brain or if Maridia is split with Botwoon...
    # A fix would be to analyze connected components using bfs, then allocate each components a number
    # of means based on its size, and run the current algorithm on each connected component.
    def random_rooms(self, n):
        """
        Partition the rooms randomly based on BFS
        Each partition grabs a neighboring tile until all the tiles are gone
        """
        tile_set = self.non_fixed()
        # choose means
        means = random.sample(self.non_fixed(), n)
        paths, partitions = bfs_partition(tile_set, means)
        for mean in means:
            self.room_walls(partitions[mean])
        return paths, partitions

    def random_rooms_alt(self, n, implicit_bboxes):
        """
        Partition the rooms randomly by merging with neighbors
        Each partition merges with a neighboring partition until the desired number of
        rooms have been created, or no more merges can be performed.
        Respects bounding boxes for rooms, so that each room's bounding box is rectangular.
        """
        tile_set = self.non_fixed()
        rooms = merging_partition(tile_set, n, 24, implicit_bboxes)
        for s in rooms.values():
            self.room_walls(s)
        return rooms

    def room_walls(self, room):
        """ puts the walls into a room, given as a set of Coord """
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

    def can_place(self, pos):
        """Can a tile be placed at pos?
        tiles can be placed at non-fixed nodes, and at empty space"""
        if pos in self.tiles:
            return not self.tiles[pos].is_fixed
        else:
            return True

    def step_on(self, pos):
        """Predicate for finding a path within the given cmap"""
        if pos in self.tiles:
            return not self.tiles[pos].is_fixed
        else:
            return False

    def sub(self, rect, relative=False):
        """Returns a subcmap which is the cmap defined by the [start, end) rectangle."""
        new_tiles = {}
        if relative:
            offset = rect.start
        else:
            offset = Coord(0, 0)
        for c in rect.as_list():
            if c in self:
                new_tiles[c - offset] = self[c]
        # new cmap's dimensions are end-start
        return ConcreteMap(rect.size_coord(), _tiles=new_tiles), rect.start

    # Behaves like a dictionary, interfacing to tiles
    def __getitem__(self, key):
        return self.tiles[key]

    # Cannot set an item outside the bounds
    def __setitem__(self, key, value):
        if key.in_bounds(Coord(0, 0), self.dimensions):
            self.tiles[key] = value
        else:
            assert False, "Index not in bounds: " + str(key)

    def __len__(self):
        return len(self.tiles)

    def __contains__(self, item):
        return item in self.tiles

    def keys(self):
        return self.tiles.keys()

    def items(self):
        return self.tiles.items()

    def values(self):
        return self.tiles.values()

#TODO
def map_lsearch(start, goal, pred=lambda x: True, dist=euclidean):
    """special search that first finds failure states in moving from start to goal,
    then moves only towards the goal to reach it, minimizing dist at each step.
    The goal here is that we can generate random, but more 'straight' paths than a random
    walk will do."""
    diff = goal - start
    pass

#TODO: possible bug where a path might be shorter than expected if
# START is encountered multiple times along the path

def get_path(offers, start, end):
    """
    Uses the offers from a bfs to construct a path
    a path is a list of consecutive states where
        1. if state a is before state b in the list, then b is reachable from a
        2. start is the first element of the list
        3. end is is the last element of the list
    Iff start and end are the same node, this returns a list of length 1
    """
    if end not in offers:
        return None
    pos = end
    path = []
    while True:
        path.append(pos)
        if pos == start:
            break
        pos = offers[pos]
    # Reverse it for a path from start to end
    return path[::-1]

def path_concat(path1, path2):
    """
    Concatenate two paths made from get_path to form a longer path
    preserves the path properties from above
    If path1 is from start1 to end1 and path2 is from end1 to end2, then
    the new path will be from start1 to end2.
    """
    assert path1[-1] == path2[0], "Incompatible paths"
    return path1[:-1] + path2

#lambda x: 0 means BFS in a heapq (first element first)
# can use random to alter the pattern of vertices grabbed by
# each mean
def bfs_partition(space, means, priority=lambda x: 0):
    """
    Actually do the partitioning for the BFS partition
    """
    # Setup
    # Key - mean, value - set of positions that mean has considered
    mfinished = {mean: set() for mean in means}
    # Key - mean, value - for position p, what made the a* offer to p?
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

# Partition algorithm that makes rooms that do not overlap
# A room overlaps with another room when they have screens that
# are in the same map position.
# In practical terms, a way to check this is that a tile designated to
# not room 1 appears in the bounding box created for the tiles of room 1,
# or more generally, if the bounding box for room 1 and any other room overlap.
# The bounding box is via "extent".
# A way to avoid this is with a "merging" partition. A map where
# every room is one screen definitely does not have this problem.
# So we start with that scenario, and merge rooms together maintaining
# the invariant that every step in the process is a set of rooms which
# do not overlap.
# Pick a random room to merge, and a random of its neighbors.
# Remove rooms for which none of their neighbors can be merged.
def merging_partition(space, targetn, maxsize, implicit_bboxes):
    """
    Partitions space into a set of "rooms" - tile sets. Targetn is the
    desired number of rooms, and maxsize is the maximum number of tiles
    that each room can occupy
    """
    # Initially, every room has only itself.
    rooms = {p: set([p]) for p in space}
    # The rooms on which forward progress can be made
    active_neighbors = collections.defaultdict(set)
    for p1, ps1 in rooms.items():
        for p2, ps2 in rooms.items():
            if p1 != p2 and adjacent(ps1, ps2):
                active_neighbors[p1].add(p2)
                active_neighbors[p2].add(p1)
    while len(rooms) > targetn:
        if len(active_neighbors) == 0:
            break
        # Pick a random active room
        r = random.choice(list(active_neighbors.keys()))
        # Pick a random of its neighbors
        n = random.choice(list(active_neighbors[r]))
        # Try to merge them
        if not can_merge(r, n, rooms, maxsize, implicit_bboxes):
            # If the merge didn't work out, then remove the neighbor
            active_neighbors[r] -= set([n])
            # If that was the last neighbor, r is no longer active.
            if len(active_neighbors[r]) == 0:
                del active_neighbors[r]
            continue
        # They can be merged...
        new_neighbors = (active_neighbors[r] | active_neighbors[n]) - set([r, n])
        # If the merged room has no active neighbors, it is no longer active
        if len(new_neighbors) == 0:
            del active_neighbors[r]
        else:
            active_neighbors[r] = new_neighbors
        rooms[r] = rooms[r] | rooms[n]
        active_neighbors = active_replace(active_neighbors, n, r)
        del rooms[n]
    return rooms

def can_merge(room1, room2, rooms, maxsize, implicit_bboxes):
    """
    Can tiles1 merge with tiles2 while respecting
    the bounding boxes and size constraints?
    """
    tiles1 = rooms[room1]
    tiles2 = rooms[room2]
    # Check that the new room won't have more than maxsize tiles
    if len(tiles1) + len(tiles2) > maxsize:
        return False
    bbox = extent(tiles1 | tiles2)
    # Check that the actual number of screens that need to be loaded
    # for the new room won't exceed maxsize.
    if bbox.area() > maxsize:
        return False
    # Build the bounding box for each room
    room_bboxes = {k: extent(v) for k, v in rooms.items()}
    # Don't care about room1 and room2, since the merge will replace them
    del room_bboxes[room1]
    del room_bboxes[room2]
    # Make sure that the bbox of the merged room does not overlap with
    # any of the existing rooms
    return not any(map(lambda b: bbox.intersects(b), list(room_bboxes.values()) + implicit_bboxes))

def active_replace(active, tile1, tile2):
    """
    When two rooms merge, their adjacencies merge
    When r1 and r2 merge into r1, go through and replace r2 in adjacencies with r1
    Replace tile1 with tile2 in active
    """
    new_active = collections.defaultdict(set)
    for k, v in active.items():
        if k != tile1:
            if tile1 in active[k]:
                new_active[k] = (active[k] - set([tile1])) | set([tile2])
            else:
                new_active[k] = active[k]
    return new_active

def active_delete(active, tile):
    """
    Remove tile from active
    """
    return {key : value - set([tile]) for (key, value) in active if key != tile}

def extent(coords):
    """Returns the smallest rectangle that contains each of the coords"""
    if len(coords) == 0:
        return None
    minx = min(coords, key=lambda item: item.x).x
    miny = min(coords, key=lambda item: item.y).y
    maxx = max(coords, key=lambda item: item.x).x
    maxy = max(coords, key=lambda item: item.y).y
    return Rect(Coord(minx, miny), Coord(maxx, maxy) + Coord(1, 1))

def adjacent(room1, room2):
    """
    Simple inefficient test for room ajdacency
    Adjacent rooms can be merged.
    """
    for p1 in room1:
        for p2 in room2:
            if p1.adjacent(p2):
                return True
    return False
