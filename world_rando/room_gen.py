import itertools

from sm_rando.world_rando.room_dtypes import *
from sm_rando.world_rando.room_utils import *
from sm_rando.world_rando.coord import *
from sm_rando.world_rando.util import *
from sm_rando.data_types import basicgraph

# Room Generation:

# takes d: a -> [b] to
# b -> a, assuming distinct b
def reverse_list_dict(d):
    reverse = {}
    for (k, vl) in d.items():
        for v in vl:
            reverse[v] = k
    return reverse

# Room tiles is room_id -> [MCoord]
def room_setup(room_tiles, cmap):
    rooms = {}
    for room_id, coord_set in room_tiles.items():
        room_bbox = extent(coord_set)
        room_cmap, room_pos = cmap.sub(room_bbox, relative=True)
        rooms[room_id] = Room(room_cmap, room_bbox.size_coord(), room_id, room_pos)
    return rooms

#TODO: work in progress
# Tile rooms is Coord -> room id,
# paths is [(start_node, end_node, [MCoord])]
# rooms is room_id -> room
def room_graphs(rooms, tile_rooms, paths):
    #TODO: node_locs for each node and each door node.
    # room_node_locs: room_id -> node -> Coord
    for (start, end, path) in paths:
        room_start = tile_rooms[path[0]]
        room_end = tile_rooms[path[-1]]
        gstart = rooms[room_start].graph
        if start not in gstart.nodes:
            rooms[room_start].items.append(Item(start, path[0] - rooms[room_start].pos))
            gstart.add_node(start)
        gend = rooms[room_end].graph
        if end not in gend.nodes:
            rooms[room_end].items.append(Item(end, path[-1] - rooms[room_end].pos))
            gend.add_node(end)
        current_room = room_start
        current_node = start
        current_pos = path[0]
        for new_pos in path:
            new_room = tile_rooms[new_pos]
            if new_room != current_room:
                gcurrent = rooms[current_room].graph
                gnew = rooms[new_room].graph
                # Create a door
                # Node in the old room
                current_wr = current_pos.wall_relate(new_pos)
                current_door = str(current_room) + "_" + str(current_pos) + "_" + current_wr
                if current_door not in gcurrent.nodes:
                    gcurrent.add_node(current_door)
                    # Create a new door for current -> new
                    d = rooms[current_room].doors
                    d.append(Door(current_pos, current_wr, current_room, new_room, len(d), current_door))
                # Link the current node with the door
                gcurrent.update_edge(current_node, current_door)
                # Node in the new room
                new_wr = new_pos.wall_relate(current_pos)
                new_door = str(new_room) + "_" + str(new_pos) + "_" + new_wr
                if new_door not in gnew.nodes:
                    gnew.add_node(new_door)
                    # Create a new door for the new -> current
                    d = rooms[new_room].doors
                    d.append(Door(new_pos, new_wr, new_room, current_room, len(d), new_door))
                # set the new current room
                current_room = tile_rooms[new_pos]
                # the new current node is the door we came into the new room by
                current_node = new_door
            current_pos = new_pos
        # link the final current node with end
        gend.update_edge(current_node, end)

def make_rooms(room_tiles, cmap, paths, settings, patterns):
    rooms = room_setup(room_tiles, cmap)
    tile_rooms = reverse_list_dict(room_tiles)
    room_graphs(rooms, tile_rooms, paths)
    # ... generate map data etc ...
    for i, r in rooms.items():
        print("BEGIN: Generating room " + str(i))
        r.level = level_of_cmap(r)
        make_subrooms(r, settings, patterns)
    return rooms

# Chooses an order to search for item placements for a given item
def choose_place_order(item, placement_chances):
    ty = item.graphic
    if ty in placement_chances:
        weights = placement_chances[ty]
    else:
        weights = placement_chances["default"]
    return weighted_random_order(["chozo", "pedestal", "hidden"], weights)

#TODO: prefer searching the opposite direction from any doors entering the cmap tile (if possible)
def find_item_loc(item, room, subrooms, roots, patterns, placement_chances):
    """Determines a random item location based on first choosing randomly the
    type of place (chozo statue, pedestal, (hidden)), then finding a location based on the
    places where the appropriate setup pattern matches. Alters the level while doing so by
    placing in the required tiles for the item location."""
    places = choose_place_order(item, placement_chances)
    # Go through the places sequentially so that a pedestal positioning can be found if a chozo statue
    # positioning is not found.
    for p in places + ["hailmary"]:
        if p == "chozo":
            #TODO: in the pattern files, the setup pattern is backwards from the normal pattern...
            # Here R means that the pattern faces in the "canonical" direction
            # so that a chozo statue in the 'r' direction is in fact facing right
            # If the setup pattern matches a location that means that that location can
            # be overwritten with the pattern to produce the desired item location
            setup_pattern_r = patterns["chozo_statue_setup_l"]
            setup_pattern_l = patterns["chozo_statue_setup_r"]
            # Pattern is the actual pattern that is written to produce the desired item loc.
            pattern_l = patterns["chozo_statue_l"]
            pattern_r = patterns["chozo_statue_r"]
            # Pattern offset is where (relative to the setup pattern match) the pattern should be placed.
            pattern_offset_r = Coord(1,0)
            # Rel obstacle is a rect which are the non-cuttable squares of the pattern relative to
            # where the pattern should be placed. Used for determining where the valid cuts are when
            # generating the subrooms.
            rel_obstacle_r = Rect(Coord(0,0), Coord(4,3))
            # Rel target are the squares that allow picking up the item relative to where the
            # pattern should be placed. Used for determining what states allow picking up the item
            # when searching for a level configuration.
            rel_target_r = Rect(Coord(3,0), Coord(4,3))
            # Rel item placement is the actual positioning of the item. Used for creating the item PLM.
            rel_item_placement_r = Coord(2,0)
            item_graphic = "C"
        elif p == "pedestal":
            #TODO: technically these are the same pattern
            setup_pattern_l = patterns["pedestal_setup_l"]
            setup_pattern_r = patterns["pedestal_setup_r"]
            #TODO: what about orbs on the pedestal?
            pattern_l = patterns["pedestal_non_orb_l"]
            pattern_r = patterns["pedestal_non_orb_r"]
            pattern_offset_r = Coord(1,1)
            rel_obstacle_r = Rect(Coord(-1,0), Coord(2,2))
            rel_target_r = Rect(Coord(-1,0), Coord(2,2))
            rel_item_placement_r = Coord(0,0)
            item_graphic = "N"
        elif p == "hidden":
            setup_pattern_l = patterns["hidden_setup_l"]
            setup_pattern_r = patterns["hidden_setup_r"]
            pattern_l = patterns["hidden_l"]
            pattern_r = patterns["hidden_r"]
            pattern_offset_r = Coord(0, 1)
            rel_obstacle_r = Rect(Coord(0,0), Coord(2,1))
            rel_target_r = Rect(Coord(0,-1), Coord(1,2))
            rel_item_placement_r = Coord(0,0)
            item_graphic = "H"
        # Try a hail mary (place on a pedestal in midair) if nothing else worked.
        elif p == "hailmary":
            setup_pattern_l = patterns["hailmary_setup_l"]
            setup_pattern_l = patterns["hailmary_setup_r"]
            pattern_l = patterns["hailmary_l"]
            pattern_r = patterns["hailmary_r"]
            pattern_offset_r = Coord(0,0)
            rel_obstacle_r = Rect(Coord(0,0), Coord(3,3))
            rel_target_r = Rect(Coord(0,0), Coord(1,3))
            rel_item_placement_r = Coord(1,0)
            item_graphic = "N"
        else:
            assert False, "Bad place type: " + p
        # Choose the direction randomly (but fall through if no valid configuration is found
        # for the first direction
        directions = ["L", "R"]
        random.shuffle(directions)
        for d in directions:
            # Set up the variables so that the next part doesn't have to care about
            # which direction is being used.
            if d == "L":
                setup_pattern = setup_pattern_l
                pattern = pattern_l
                pattern_offset = pattern_offset_r * Coord(-1,0)
                rel_obstacle = rel_obstacle_r.flip_in_rect(pattern.dimensions, Coord(1,0))
                rel_target = rel_target_r.flip_in_rect(pattern.dimensions, Coord(1,0))
                rel_item_placement = rel_item_placement_r.flip_in_rect(pattern.dimensions, Coord(1,0))
            if d == "R":
                setup_pattern = setup_pattern_r
                pattern = pattern_r
                pattern_offset = pattern_offset_r
                rel_obstacle = rel_obstacle_r
                rel_target = rel_target_r
                rel_item_placement = rel_item_placement_r
            # Find the locations in the item's maptile where the setup pattern can match
            item_maptile = Rect(item.map_pos.scale(16), item.map_pos.scale(16) + Coord(16,16))
            matches = room.level.find_matches_in_rect(setup_pattern, item_maptile)
            # If there are no matches, then fall through to the next possible item placement
            # (different direction, different type of item loc)
            if len(matches) == 0:
                print("No match for: " + p + ", " + d)
                pass
            else:
                # Choose the placement of the item randomly
                c = random.choice(matches)
                # Calculate the absolute positions based on the relative positions
                pattern_placement = c + pattern_offset
                item_placement = pattern_placement + rel_item_placement
                obstacle_rect = rel_obstacle.translate(pattern_placement)
                target_rect = rel_target.translate(pattern_placement)
                # Actually make the necessary level edit
                room.level = room.level.compose(pattern, collision_policy="overwrite", offset=pattern_placement)
                # Tell the item where it is in the room and what its graphics should be.
                item.room_pos = item_placement
                item.graphic = item_graphic
                #TODO: pattern placement might not necessarily be within the subroom?
                item_subroom = find_coord(subrooms, roots, pattern_placement)
                # Add the resulting obstacle to the subroom's obstacles
                #TODO: item.name different from item.item_type
                obstacle = Obstacle(item.item_type, obstacle_rect, target_rect)
                subrooms[item_subroom].place_obstacle(obstacle)
                print("Found location for: " + p + ", " + d)
                # Once the location is found, just stop.
                return
    assert False, "No item placement found!"

#TODO: doors should generate their own obstacle when they are created?
# same with their own pattern?
#TODO: doors should have a map_pos and a room_pos just like items
def mk_door_obstacles(room):
    obstacles = []
    for door in room.doors:
        map_pos = door.pos - room.pos
        room_pos = find_door_pos(map_pos, door.direction)
        direction = door.direction
        #TODO: some way to have this as a construct rather than writing it out every time...
        if direction == "U":
            obstacle_rect_rel = Rect(Coord(0,0), Coord(4,2))
            target_rect_rel = Rect(Coord(0,0), Coord(4,1))
        elif direction == "D":
            obstacle_rect_rel = Rect(Coord(0,0), Coord(4,2))
            target_rect_rel = Rect(Coord(0,1), Coord(4,2))
        elif direction == "L":
            obstacle_rect_rel = Rect(Coord(0,0), Coord(2,4))
            target_rect_rel = Rect(Coord(0,0), Coord(1,4))
        elif direction == "R":
            obstacle_rect_rel = Rect(Coord(0,0), Coord(2,4))
            target_rect_rel = Rect(Coord(1,0), Coord(2,4))
        else:
            assert False, "Bad direction: " + str(direction)
        obstacle_rect = obstacle_rect_rel.translate(room_pos)
        target_rect = target_rect_rel.translate(room_pos)
        door_obstacle = Obstacle(door.name, obstacle_rect, target_rect)
        obstacles.append(door_obstacle)
    return obstacles

def make_subrooms(room, settings, patterns):
    door_obstacles = mk_door_obstacles(room)
    # Partition into subrooms avoiding doors
    print("Creating subrooms")
    max_parts = settings["max_room_partitions"]
    min_part_size = settings["min_room_partition_size"]
    roots, subrooms = subroom_partition(room, max_parts, min_part_size, door_obstacles)
    print("Final subrooms:")
    print_subrooms(subrooms)
    subroom_leaves = find_leaves(subrooms, roots)
    # DEBUG: view the map
    room.viz_cmap("./output/")
    # Fill the walls so that the item generation will know where to look
    make_subroom_walls(room.level, subroom_leaves)
    # DEBUG: look at the level data
    room.viz_level("./output/")
    # Generate item locations
    print("Generating item locations")
    placement_chances = settings["item_placement_chances"]
    for i in room.items:
        print("Item: " + i.item_type)
        find_item_loc(i, room, subrooms, roots, patterns, placement_chances)
    # Generate the graph
    print("Generating subroom adjacencies")
    subroom_graph = subroom_adjacency_graph(subroom_leaves)
    min_entrance_size = settings["min_room_entrance_size"]
    max_entrance_size = settings["max_room_entrance_size"]
    #subroom_graph.visualize("./output/room" + str(room.room_id) + "subroom_graph")
    print("Embedding room graph")
    t = embed_room_graph(room.graph, subroom_graph, min_entrance_size, max_entrance_size)
    detailed_room_graph, subroom_nodes, used_subrooms = t
    unused_subrooms = filter(lambda x: x.id not in used_subrooms, subroom_leaves)
    #TODO: this is kind of messy
    print("Finishing up subroom generation.")
    # Fill the walls again (now with entrances)
    make_subroom_walls(room.level, subroom_leaves)
    # Fill unused subrooms
    for r in unused_subrooms:
        mk_default_rect(room.level, r.rect)
    # Add relevant info to the room
    room.detailed_room_graph = detailed_room_graph
    room.subroom_nodes = subroom_nodes

class Adjacency(object):

    # subroom_id is which subroom this adj abuts
    def __init__(self, id1, id2, rect, direction, impassables=None, entrances=None):
        self.id1 = id1
        self.id2 = id2
        self.rect = rect
        self.direction = direction
        if impassables is not None:
            self.impassables = impassables
        else:
            self.impassables = []
        if entrances is not None:
            self.entrances = entrances
        else:
            self.entrances = []

    #TODO: self.impassables might not be correct
    def split(self, id2, index, direction, new_id1, new_id2):
        print("split_rect: ", self.rect)
        print(index, direction)
        r1, r2 = self.rect.split(index, direction)
        a1 = Adjacency(new_id1, id2, r1, self.direction, self.impassables)
        a2 = Adjacency(new_id2, id2, r2, self.direction, self.impassables)
        return a1, a2

    def is_between(self, o_id1, o_id2):
        a = (self.id1 == o_id1 and self.id2 == o_id2)
        b = (self.id1 == o_id2 and self.id2 == o_id1)
        print("between")
        print(self.id1, self.id2)
        print(a,b)
        return a or b

    def get_other_id(self, subroom_id):
        if self.id1 == subroom_id:
            return self.id2
        elif self.id2 == subroom_id:
            return self.id1
        else:
            assert False, "This is not an adjacency of subroom {}".format(subroom_id)

    def replace_id(self, old_id, new_id):
        if self.id1 == old_id:
            self.id1 = new_id
        elif self.id2 == old_id:
            self.id2 = new_id
        else:
            assert False, "This is not an adjacency of subroom {}".format(subroom_id)

    def add_impassable(self, impassable):
        self.impassables.append(impassable)

    # List of rectangles which can be used to make an entrance that is
    # at least as large as min_size
    def find_passables(self, min_size):
        rects = [self.rect]
        new_rects = []
        # Cut every rectangle with each impassable rect
        for i_direction, i_rect in self.impassables:
            for r in rects:
                new_rects.append(r.cut(i_rect, i_direction, min_size))
            rects = new_rects
        new_rects = []
        # Also cut them with the entrances since the new rect can't go on top
        # of the entrance
        #TODO Technically it can...
        for e_rect in self.entrances:
            for r in rects:
                #TODO: is self.direction correct?
                new_rects.append(r.cut(e_rect, self.direction, min_size))
            rects = new_rects
        return rects

    def find_non_entrances(self):
        rects = [self.rect]
        new_rects = []
        for e_rect in self.entrances:
            for r in rects:
                #TODO: is self.direction correct?
                new_rects.extend(r.cut(e_rect, self.direction, 1))
            rects = new_rects
        return rects

    #TODO: entrances to morph subrooms can be as small as 1...
    #TODO: need to add an impassable where the adjacency intersects the
    # wall of the room...
    def add_entrance(self, min_size, max_size):
        # The long axis of the adjacency is perpendicular to its direction
        axis = Coord(1,1) - self.direction
        passables = self.find_passables(min_size)
        print("Self size:")
        print(self.rect)
        print("Passables:")
        print(passables)
        weights = [p.area() for p in passables]
        p = random.choices(passables, weights)[0]
        #TODO: this is not correct - the entrance we add should fit entirely within
        # the passable we decided to use...
        adj_size = self.rect.size(axis)
        passable_size = p.size(axis)
        entrance_size = random.randrange(min_size, min(max_size, passable_size))
        entrance_placement = random.randrange(adj_size - entrance_size)
        entrance_start = self.rect.start + axis.scale(entrance_placement)
        entrance_end = entrance_start + axis.scale(entrance_size) + self.direction.scale(2)
        entrance = Rect(entrance_start, entrance_end)
        self.entrances.append(entrance)
        return entrance

    #BUG: index out of bounds!
    #TODO: only make the side of the wall that abuts the larger of the two rooms
    # so that the smaller one gets some more space.
    def mk_wall(self, level):
        for r in self.find_non_entrances():
            mk_default_rect(level, r)
        #TODO: implement entrance types
        for e in self.entrances:
            mk_air_rect(level, e)

class Obstacle(object):

    def __init__(self, name, obstacle_rect, target_rect):
        self.name = name
        self.obstacle_rect = obstacle_rect
        self.target_rect = target_rect

class SubroomNode(object):

    def __init__(self, id, rect, adjacencies, obstacles):
        self.id = id
        self.rect = rect
        self.adj = adjacencies
        self.obstacles = obstacles
        self.children = []

    def subdivide(self, index, direction, id1, id2, subrooms):
        """Divide a room at index in the given direction. Cutting a room in the x-direction
        means that the horizontal axis of the room is divided by the cut. Coords of the room
        /before/ index will belong to the first part, while coords of the room at or after index
        will belong to the second part."""
        self.check_inbounds(index, direction)
        # Compute the rectangles that each child will take up
        rect1, rect2 = self.rect.split(index, direction)
        print("SUBROOM: partitioning subroom {}".format(self.id))
        print("rects: ", self.rect)
        # Compute the adjacencies that each child will have
        #TODO: can simplify this with Rect.within
        adj1 = []
        adj2 = []
        for a in self.adj:
            # The other SubroomNode implicated in this adjacency
            o_id = a.get_other_id(self.id)
            other = subrooms[o_id]
            assert other.is_leaf()
            # child1 takes left/top adjacencies
            if a.direction == direction.neg():
                # As long as adjacencies are always shared between neighbors,
                # this will also update the neighbors' adjacency
                a.replace_id(self.id, id1)
                adj1.append(a)
            # child2 takes right/bottom adjacencies
            elif a.direction == direction:
                a.replace_id(self.id, id2)
                adj2.append(a)
            else:
                # Find where the cut is being made
                dp = self.div_point(index, direction)
                d_index = dp.index(direction)
                # If it ends before the cut point, it belongs to child1
                if a.rect.end.index(direction) <= d_index:
                    a.replace_id(self.id, id1)
                    adj1.append(a)
                # If it starts after the cut point, it belongs to child2
                elif a.rect.start.index(direction) >= d_index:
                    a.replace_id(self.id, id2)
                    adj2.append(a)
                # If neither, it must be split
                else:
                    # Where the cut is relative to the start of the adjacency
                    index_within_adj = (dp - a.rect.start).index(direction)
                    print(index, index_within_adj)
                    # Make the cut
                    a1, a2 = a.split(other.id, index_within_adj, direction, id1, id2)
                    adj1.append(a1)
                    adj2.append(a2)
                    # Also replace the neighbor's adjacency
                    other.replace_adj(self.id, [a1, a2])
        # Add an adjacency between the two children along the newly created edge
        dp = self.div_point(index, direction)
        op = self.obv_point(index, direction)
        a = Adjacency(id1, id2, Rect(dp - direction, op + direction), direction)
        #print("between rect: ", a.rect)
        adj1.append(a)
        adj2.append(a)
        # Assign obstacles the same way as adjacencies
        obs1 = []
        obs2 = []
        for o in self.obstacles:
            if o.obstacle_rect.within(rect1):
                obs1.append(o)
            elif o.obstacle_rect.within(rect2):
                obs2.append(o)
            else:
                assert False, "Obstacle split by subdivide: " + str(o)
        child1 = SubroomNode(id1, rect1, adj1, obs1)
        child2 = SubroomNode(id2, rect2, adj2, obs2)
        self.children = [id1, id2]
        subrooms[id1] = child1
        subrooms[id2] = child2

    def is_leaf(self):
        return len(self.children) == 0

    def find_adj(self, other_id):
        """Find the adjacency with the given id"""
        the_adj = [i for i in self.adj if i.is_between(self.id, other_id)]
        print("find_adj", [a.rect for a in the_adj])
        assert len(the_adj) == 1
        return the_adj[0]

    #TODO: not proof against multiple adjs with the same id pairs
    def find_adj_index(self, id):
        for i, a in enumerate(self.adj):
            if a.is_between(self.id, id):
                return i
        assert False, "No adjacency"

    def reassign_adj(self, old_id, new_id):
        """Reassign the id of an adjacency"""
        a = self.find_adj(old_id)
        a.replace_id(old_id, new_id)

    def replace_adj(self, id, new_adjs):
        """Replace an ajdacency with new ones"""
        self.remove_adj(id)
        self.adj.extend(new_adjs)

    def remove_adj(self, adj_id):
        i = self.find_adj_index(adj_id)
        self.adj.pop(i)

    def place_obstacle(self, obstacle):
        self.obstacles.append(obstacle)
        change_borders = obstacle.obstacle_rect.borders()
        for rect, direction in change_borders:
            adj_to_cut = [a for a in self.adj if a.direction == direction and rect.within(a.rect)]
            for a in adj_to_cut:
                a.add_impassable(rect)

    def div_point(self, index, direction):
        return self.rect.start + direction.scale(index)

    def obv_point(self, index, direction):
        return self.div_point(index, direction) + ((Coord(1,1) - direction) * (self.rect.end - self.rect.start))

    def size(self):
        """Returns the total number of places a cut could be made in self."""
        return self.rect.perimeter() / 2

    def as_set(self):
        return self.rect.as_set()

    def check_inbounds(self, index, direction):
        """Check that the proposed cut is in-bounds."""
        div_point = self.div_point(index, direction)
        assert self.rect.coord_within(div_point)

    def check_valid(self, index, direction, min_size):
        """Checks that a cut can be made at the given index in the given direction
        if the smallest size of a subroom is min_size. Fails with assertion if the
        cut is outside of range, returns False if the cut is within range but would
        result in a room that is too small."""
        self.check_inbounds(index, direction)
        #TODO: kind of wasteful to compute these things again...
        div_point = self.div_point(index, direction)
        obv_point = self.obv_point(index, direction)
        dp = div_point.index(direction)
        startpoint = self.rect.start.index(direction)
        endpoint = self.rect.end.index(direction)
        print("SUBROOM: considering partition")
        print(self.rect)
        print(startpoint, dp, endpoint)
        if dp - startpoint < min_size or endpoint - dp < min_size:
            print("SUBROOM: Cut rejected - too small")
            return False
        # a 2xX rectangle indicating where the walls of the proposed cut will appear
        cut_rect = Rect(div_point - direction, obv_point + direction)
        # Check obstacles:
        for o in self.obstacles:
            if o.obstacle_rect.intersects(cut_rect):
                print("SUBROOM: Cut rejected - intersects an obstacle")
                return False
        print("SUBROOM: Cut accepted")
        return True

    def choose_cut(self):
        """Randomly choose a possible cut."""
        directions = [Coord(1,0), Coord(0,1)]
        # Get the horizontal and vertical size of the direction
        sizes = [self.rect.size(d) for d in directions]
        ds = list(zip(directions, sizes))
        direction, size = random.choices(ds, sizes)[0]
        index = random.randrange(size)
        return index, direction

def find_coord(subrooms, roots, coord):
    """Find which leaf subroom has the given coord."""
    curr_roots = roots
    while True:
        candidates = [r for r in curr_roots if subrooms[r].rect.coord_within(coord)]
        assert len(candidates) == 1
        candidate_id = candidates[0]
        candidate = subrooms[candidate_id]
        if candidate.is_leaf():
            break
        else:
            curr_roots = candidate.children
    return candidate_id

def find_leaves(subrooms, roots):
    """Return a list of the ids of the leaves of the given subroom tree."""
    # Note: will not terminate if there is a cycle in the subroom tree
    # (hopefully there isn't because it's supposed to be a TREE)
    leaves = []
    new_roots = []
    while len(roots) != 0:
        for r in roots:
            r_node = subrooms[r]
            if r_node.is_leaf():
                leaves.append(r_node)
            else:
                new_roots.extend(r_node.children)
        roots = new_roots
        new_roots = []
    return leaves

def subroom_adjacency_graph(subroom_leaves):
    g = basicgraph.BasicGraph()
    # Add a node for each subroom and each obstacle that holds the target region of the obstacle
    for leaf in subroom_leaves:
        leaf_name = str(leaf.id)
        g.add_node(leaf_name)
        # Add an edge between each obstacle and the leaf that contains it.
        for o in leaf.obstacles:
            g.add_node(o.name, data=o)
            g.add_edge(leaf_name, o.name)
            g.add_edge(o.name, leaf_name)
    # Once all the subrooms have been added, produce the adjacencies
    for leaf in subroom_leaves:
        for neighbor_adj in leaf.adj:
            leaf_name = str(leaf.id)
            other_name = str(neighbor_adj.get_other_id(leaf.id))
            g.add_edge(leaf_name, other_name, data=neighbor_adj)
    return g

def embed_room_graph(room_graph, subroom_graph, min_entrance_size, max_entrance_size):
    """Embed the room graph into the subroom graph, resulting in a new graph
    which is the graph that will actually be searched over during subroom generation."""
    # Key - subroom_id, value - list of nodes belonging to that subroom
    # Used to create a subgraph when building the subroom
    subroom_nodes = collections.defaultdict(list)
    # The subrooms which the graph embedding actually uses
    # Used to calculate the subrooms which are completely unused.
    used_subrooms = set()
    g = basicgraph.BasicGraph()
    for node1, node2 in room_graph.get_edges():
        itemset = room_graph.get_edge_data(node1, node2)
        #TODO: randomized DFS?
        finished, offers = subroom_graph.DFS(node1, node2)
        path = basicgraph.bfs_path(offers, node1, node2)
        current_node = None
        for first, second in zip(path, path[1:]):
            if first in room_graph:
                # First is an obstacle node
                # Copy the data: the rectangle of actual tiles that this obstacle represents
                #TODO: might only want the last two entries: the target squares
                if first not in g:
                    g.add_node(first, data=subroom_graph.nodes[first].data)
                current_node = first
            elif second in room_graph:
                # Second is an obstacle node
                if second not in g:
                    g.add_node(second, data=subroom_graph.get_data[second])
                current_node = second
            else:
                # edge between two subroom nodes
                edge_fs = subroom_graph.get_edge_data(first, second)
                edge_sf = subroom_graph.get_edge_data(second, first)
                fs_name = str(first) + "-" + str(second)
                sf_name = str(second) + "-" + str(first)
                # Add a node for the exit to the old subroom and the entrance to the new one
                if fs_name not in g:
                    # subroom interface nodes should only be added two at a time
                    assert sf_name not in g
                    # Choose a place to break the wall between the two subrooms
                    #TODO: Decide the type of each entrance based on what items are available
                    e = edge_fs.add_entrance(min_entrance_size, max_entrance_size)
                    # Create a node in the first subroom
                    g.add_node(fs_name, data=e)
                    subroom_nodes[first].append(fs_name)
                    used_subrooms.add(first)
                    # Create a node in the second subroom
                    g.add_node(sf_name, data=e)
                    subroom_nodes[second].append(sf_name)
                    used_subrooms.add(second)
                # Regardless of what type of node, connect them up
                # TODO: update edge append instead!
                g.add_edge_append(current_node, fs_name, data=itemset)
                g.add_edge_append(fs_name, sf_name, data=itemset)
                current_node = fs_name
    return g, subroom_nodes, used_subrooms

def make_subroom_walls(level, subroom_leaves):
    for leaf in subroom_leaves:
        for a in leaf.adj:
            a.mk_wall(level)

def print_subrooms(subrooms):
    for s1 in subrooms.values():
        if s1.is_leaf():
            print("{} : {}".format(s1.id, s1.rect))
            for a in s1.adj:
                print("\t {} , {}, {}".format(a.id1, a.id2, a.rect))

# Contintue to partition until EACH subroom fails a partition (because it is too small,
# or intersects an obstacle)
def subroom_partition(room, max_parts, min_partsize, obstacles):
    """Creates a partition of the room into subrooms."""
    # First, generate a greedy rectangularization of the concrete map for the room
    print("PART: Finding rectangularization")
    current_id, roots, subrooms = rectangularize(room.cmap, obstacles)
    print("PART: Generating partitions")
    while True:
        print("PART: subrooms")
        print_subrooms(subrooms)
        print("end subrooms")
        current_children = roots
        # Choose a partition to subdivide
        while len(current_children) != 0:
            current_nodes = [subrooms[i] for i in current_children]
            weights = [i.size() for i in current_nodes]
            current_node = random.choices(current_nodes, weights)[0]
            if current_node.is_leaf():
                break
            else:
                current_children = current_node.children
        # choose an x or a y to subdivide it at
        index, direction = current_node.choose_cut()
        # break if the xy is invalid
        #   - causes a partition area to be too small
        #   - goes through an obstacle like a door
        #   - creates a partition over the max
        if current_node.check_valid(index, direction, min_partsize):
            id1 = current_id
            current_id += 1
            id2 = current_id
            current_id += 1
            current_node.subdivide(index, direction, id1, id2, subrooms)
        else:
            break
    return roots, subrooms

#TODO: parameterized by direction in both x and y
# i.e. which corner to start from.
def rectangularize(cmap, obstacles):
    subrooms = {}
    # Stores the set of CMAP tiles for each subroom
    subroom_sets = {}
    roots = []
    current_id = 0
    # Sorts topmost leftmost
    positions = sorted(cmap.keys())
    # Find rectangles until the entire cmap is covered
    print("RECT: Finding rectangles")
    while len(positions) > 0:
        pos = positions[0]
        rect = find_rect(positions, pos)
        for c in rect.as_list():
            #BUG: x not in list
            positions.remove(c)
        #TODO: rects are not relative to the room position, but they should be...
        print(rect)
        # Add it to the subroom tree, and convert its size and position into the level format
        subrooms[current_id] = SubroomNode(current_id, rect.scale(16), [], [])
        subroom_sets[current_id] = rect.as_set()
        roots.append(current_id)
        current_id += 1
    # Find adjacencies between the rectangles
    print("RECT: Finding adjacencies")
    for r1, r2 in itertools.combinations(roots, 2):
        # Since positions was sorted and the combinations function
        # outputs tuples in sorted order, r_1 is above / to the left of r_2
        adj = add_adjacency(subrooms[r1], subroom_sets[r1], subrooms[r2], subroom_sets[r2])
    # Assign the obstacles
    print("RECT: Assigning obstacles")
    for o in obstacles:
        done = False
        for s in subrooms.values():
            # If the object is contained by the subroom...
            if o.obstacle_rect.within(s.rect):
                s.obstacles.append(o)
                done = True
                break
        if not done:
            assert False, "Obstacle not contained by a single subroom: " + str(o.obstacle_rect)
    return current_id, roots, subrooms

def add_adjacency(r1, r1_set, r2, r2_set):
    # D R L U
    directions = [Coord(0,1), Coord(1,0), Coord(-1,0), Coord(0,-1)]
    for d in directions:
        neighbors = sorted([p + d for p in r1_set if p + d not in r1_set and p + d in r2_set])
        if len(neighbors) > 0:
            # The top left corner of the topmost leftmost neighbor
            tl_neighbor = neighbors[0].scale(16)
            # The top left corner of the cell directly adjacent to the topmost
            # leftmost neighbor (in direction d)
            tl_self = tl_neighbor + d.scale(-16)
            if tl_neighbor < tl_self:
                tl1 = tl_neighbor
                tl2 = tl_self
            else:
                tl1 = tl_self
                tl2 = tl_neighbor
            da = d.abs()
            # Perpendicular to da and also positive
            pa = Coord(1,1) - d.abs()
            dist = 16 * len(neighbors)
            start = tl1 + da.scale(15)
            end = start + pa.scale(dist) + da.scale(2)
            rect = Rect(start, end)
            a = Adjacency(r1.id, r2.id, rect, da)
            r1.adj.append(a)
            r2.adj.append(a)
            return
        # They do not border each other
        else:
            pass

#TODO: this is less efficient than search-based methods.
def find_rect(positions, pos):
    assert pos in positions
    print("FIND: finding best rectangle for " + str(pos))
    # The current best rectangle
    best_rect = Rect(pos, pos + Coord(1,1))
    # The set of all coords that represent the bottom left corner of a rectangle that contains pos
    # and doesn't include squares not in positions
    tried = set([pos])
    # Whether or not we found a useful rectangle on this iteration
    new = True
    y_start = 1
    n = 2
    # While trying larger rectangles will produce results
    while new:
        new = False
        start_pos = pos + Coord(0,1).scale(y_start)
        # Move up the diagonal from start_pos and check each rectangle
        for i in range(n):
            p = start_pos + Coord(1,-1).scale(i)
            l = p - Coord(1,0)
            u = p - Coord(0,1)
            check_left = l in tried or l.x < pos.x
            check_up = u in tried or u.y < pos.y
            if p in positions and check_left and check_up:
                new = True
                tried.add(p)
                r = Rect(pos, p + Coord(1,1))
                if r.area() > best_rect.area():
                    best_rect = r
        n += 1
        y_start += 1
    return best_rect

# Translates the (uncompressed) leveldata bytes to a level dictionary.
# levelsize is the number of bytes in the decompressed level1 data
# = 2 * the number of BTS bytes
# = the number of level2 bytes
def level_from_bytes(levelbytes, dimensions):
    # First two bytes are the amount of level1 data
    levelsize = int.from_bytes(levelbytes[0:2], byteorder='little')
    # Cut off the size
    levelbytes = levelbytes[2:]
    # Make sure everything matches
    assert levelsize % 2 == 0, "Purported level size is not even length"
    assert levelsize == dimensions.x * dimensions.y * 2, "Level data length does not match specified room dimensions"
    # The level might not include level2 data
    if len(levelbytes) == int(2.5 * levelsize):
        has_level2 = True
    elif len(levelbytes) == int(1.5 * levelsize):
        has_level2 = False
    else:
        assert False, "Purported level size does not match actual level size"
    level = Level(dimensions)
    for y in range(dimensions.y):
        for x in range(dimensions.x):
            index = y * dimensions.x + x
            level1index = index * 2
            level1 = int.from_bytes(levelbytes[level1index:level1index+2], byteorder='little')
            btsindex = index + levelsize
            bts = int.from_bytes(levelbytes[btsindex:btsindex+1], byteorder='little')
            if has_level2:
                level2index = index + (3*levelsize/2)
                level2 = int.from_bytes(levelbytes[level2index:level2index+2], byteorder='little')
            else:
                level2 = 0
            #TODO: level2 info dropped on the floor
            
            ttype = level1 >> 12
            hflip = (level1 >> 11) & 1
            vflip = (level1 >> 10) & 1
            tindex = level1 & 0b1111111111
            texture = Texture(tindex, (hflip, vflip))
            tiletype = Type(ttype, bts)
            level[Coord(x,y)] = Tile(texture, tiletype)
    return level

