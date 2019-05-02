from .room_dtypes import *
from .room_utils import *
from .coord import *
from .util import *
from data_types import basicgraph

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
        lower, upper = extent(coord_set)
        room_cmap, room_pos = cmap.sub(lower, upper + Coord(1,1))
        size = upper + Coord(1,1) - lower
        rooms[room_id] = Room(room_cmap, size, room_id, room_pos)
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
                    d.append(Door(current_pos, current_wr, current_room, new_room, len(d)))
                # Link the current node with the door
                gcurrent.update_edge(current_node, current_door)
                # Node in the new room
                new_wr = new_pos.wall_relate(current_pos)
                new_door = str(new_room) + "_" + str(new_pos) + "_" + new_wr
                if new_door not in gnew.nodes:
                    gnew.add_node(new_door)
                    # Create a new door for the new -> current
                    d = rooms[new_room].doors
                    d.append(Door(new_pos, new_wr, new_room, current_room, len(d)))
                # set the new current room
                current_room = tile_rooms[new_pos]
                # the new current node is the door we came into the new room by
                current_node = new_door
            current_pos = new_pos
        # link the final current node with end
        gend.update_edge(current_node, end)

def make_rooms(room_tiles, cmap, paths):
    rooms = room_setup(room_tiles, cmap)
    tile_rooms = reverse_list_dict(room_tiles)
    room_graphs(rooms, tile_rooms, paths)
    # ... generate map data etc ...
    for r in rooms.values():
        r.level_data = level_of_cmap(r)
    return rooms

# Chooses an order to search for item placements for a given item
def choose_place_order(item, placement_chances):
    ty = item.item_type
    if ty in placement_chances:
        weights = placement_chances[ty]
    else:
        weights = placement_chances["default"]
    return weighted_random_order(["chozo", "pedestal", "hidden"], weights)

#TODO: Needs to also remove part of an adjacency in the subroom list and
# add its own obstacle to the subroom's obstacle list
def find_item_loc(item, room, patterns, placement_chances):
    """Determines a random item location based on first choosing randomly the
    type of place (chozo statue, pedestal, (hidden)), then finding a location based on the
    places where the appropriate setup pattern matches. Alters the level while doing so by
    placing in the required tiles for the item location."""
    places = choose_place_order(item, placement_chances)
    # Go through the places sequentially so that a pedestal positioning can be found if a chozo statue
    # positioning is not found.
    for p in places:
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
        elif p == "hidden":
            assert False, "Not implemented!"
        directions = random.shuffle(["L", "R"])
        # Choose the direction randomly (but fall through if no valid configuration is found
        # for the first direction
        for d in directions:
            # Set up the variables so that the next part doesn't have to care about
            # which direction is being used.
            if d == "L":
                setup_pattern = setup_pattern_l
                pattern = pattern_l
                offset = pattern_offset_r * Coord(-1,0)
                rel_obstacle = rel_obstacle_r.flip(Coord(1,0))
                rel_target = rel_target_r.flip(Coord(1,0))
                rel_item_placement = rel_item_placement_r * Coord(-1, 0)
            if d == "R":
                setup_pattern = setup_pattern_r
                pattern = pattern_r
                pattern_offset = pattern_offset_r
                rel_obstacle = rel_obstacle_r
                rel_target = rel_target_r
                rel_item_placement = rel_item_placement_r
            # Find the locations in the room where the setup pattern can match
            # TODO: find only the matches within the map square given by the item's map location!
            matches = room.level.find_matches(setup_pattern)
            # If there are no matches, then fall through to the next possible item placement
            # (different direction, different type of item loc)
            if len(matches) == 0:
                pass
            else:
                # Choose the placement of the item randomly
                c = random.choice(matches)
                # Calculate the absolute positions based on the relative positions
                pattern_placement = c + pattern_offset
                item_placement = pattern_placement + rel_item_placement
                obstacle = rel_obstacle.translate(pattern_placement)
                target = rel_target.translate(pattern_placement)
                # Actually make the necessary level edit
                room.level = room.level.compose(pattern, offset=pattern_placement)
                # Tell the item where it is in the room
                #TODO: also tell the item what type of item to be
                item.room_pos = item_placement
                # Return the obstacle definition for the item location
                return (obstacle, target, item.name)
        else:
            assert False, "Bad place type: " + p
    assert False, "No item placement found!"

def make_subrooms(room):
    #TODO: Generate obstacles for doors
    # Partition into subrooms
    roots, subrooms = subroom_partition(room, 20, 5, obstacles)
    #TODO: Generate obstacles for rooms using find_item loc
    subroom_leaves = find_leaves(subrooms)
    subroom_graph = subroom_adjacency_graph(subroom_leaves)
    detailed_room_graph, subroom_nodes, used_subrooms, entrances = embed_room_graph(room.graph, subroom_graph)
    unused_subrooms = filter(lambda x: x.id not in used_subrooms, subroom_leaves)
    # Fill the walls
    make_subroom_walls(room.level, subroom_leaves)
    # Unfill the subroom entrances
    #TODO: Decide the type of each entrance based on what items are available
    # and fill with the appropriate block type
    for e in entrances:
        room_utils.mk_air_rect(room.level, e[0], e[1])
    # Fill unused subrooms
    for r in unused_subrooms:
        room_utils.mk_default_rect(room.level, r.rect[0], r.rect[1])
    # Add relevant info to the room
    room.detailed_room_graph = detailed_room_graph
    room.subroom_nodes = subroom_nodes

class SubroomNode(object):

    def __init__(self, id, rect, adjacencies, obstacles):
        self.id = id
        self.rect = rect
        self.adj = adjacencies
        self.obstacles = obstacles
        self.children = []

    # an adjacency is a 3-tuple of (id, rect, direction)
    # an obstacle is a 3-tuple of (name, obstacle_rect, target_rect)
    def subdivide(self, index, direction, id1, id2, subrooms):
        """Divide a room at index in the given direction. Cutting a room in the x-direction
        means that the horizontal axis of the room is divided by the cut. Coords of the room
        /before/ index will belong to the first part, while coords of the room at or after index
        will belong to the second part."""
        self.check_inbounds(index, direction)
        # Compute the rectangles that each child will take up
        rect1, rect2 = self.rect.split(index, direction)
        # Compute the adjacencies that each child will have
        #TODO: can simplify this with Rect.within
        adj1 = []
        adj2 = []
        for a in self.adjacencies:
            # The other SubroomNode implicated in this adjacency
            other = subrooms[a[0]]
            # child1 takes left/top adjacencies
            if a[2] == direction.neg():
                adj1.append(a)
                # Reassign the old ajdancency for the neighbor
                other.reassign_adj(self.id, id1)
            # child2 takes right/bottom adjacencies
            if a[2] == direction:
                adj2.append(a)
                other.reassign_adj(self.id, id2)
            else:
                # If it ends before the index, it belongs to child1
                if a.end.index(direction) < index:
                    adj1.append(a)
                    other.reassign_adj(self.id, id1)
                # If it starts after the index, it belongs to child2
                elif a.start.index(direction) > index:
                    adj1.append(a)
                    other.reassign_adj(self.id, id2)
                # If neither, it must be split
                else:
                    ar1, ar2 = a.split(index, direction)
                    a1 = (a[0], ar1, a[2])
                    a2 = (a[0], ar2, a[2])
                    adj1.append(a1)
                    adj2.append(a2)
                    # Also split the neighbor's adjacency
                    other.split_adj(self.id, id1, id2, index, direction)
        # Add an adjacency between the two children along the newly created edge
        dp = self.div_point(index, direction)
        op = self.obv_point(index, direction)
        adj1.append((id2, dp - direction, op - direction, direction))
        adj2.append((id1, dp, op, direction.scale(-1)))
        # Assign obstacles the same way as adjacencies
        obs1 = []
        obs2 = []
        for o in self.obstacles:
            if o.within(rect1):
                obs1.append(o)
            elif o.within(rect2):
                obs2.append(o)
            else:
                assert False, "Obstacle split by subdivide: " + str(o)
        child1 = SubroomNode(id1, rect1, adj1, obs1)
        child2 = SubroomNode(id2, rect2, adj2, obs2)
        self.children = [child1, child2]

    def is_leaf(self):
        return len(self.children) == 0

    def find_adj(self, id):
        """Find the adjacency with the given id"""
        the_adj = [i for i in self.adj if i[0] == id]
        assert len(the_adj) == 1
        return the_adj[0]

    def reassign_adj(self, old_id, new_id):
        new_adj = self.find_adj(old_id)
        new_adj[0] = new_id
        self.adj = [i for i in other.adj if i[0] != old_id] + [new_adj]

    def split_adj(self, old_id, new_id1, new_id2, index, direction):
        adj = self.find_adj(old_id)
        new_r1, new_r2 = adj[1].split_rect(index, direction)
        new_1 = (id1, new_r1, adj[2])
        new_2 = (id2, new_r2, adj[2])
        self.adj = [i for i in other.adj if i[0] != old_id] + [new_1, new_2]

    def div_point(self, index, direction):
        return self.rect.start + direction.scale(index)

    def obv_point(self, index, direction):
        return self.div_point() + (Coord(1,1) - d) * self.rect.end

    def size(self):
        """Returns the total number of places a cut could be made in self."""
        return self.rect.perimeter / 2

    def as_set(self):
        return self.rect.as_set()

    def check_inbounds(index, direction):
        """Check that the proposed cut is in-bounds."""
        div_point = self.div_point()
        assert self.rect.coord_within(div_point)

    def check_valid(index, direction, min_size):
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
        endpoint = self.rect.start.index(direction)
        if dp - startpoint < min_size:
            return False
        if endpoint - dp < min_size:
            return False
        # a 2xX rectangle indicating where the walls of the proposed cut will appear
        cut_rect = Rect(div_point - d, obv_point + d)
        # Check obstacles:
        for o in self.obstacles:
            #
            if o[1].intersects(cut_rect):
                return False
        return True

    def choose_cut(self):
        """Randomly choose a possible cut."""
        directions = [Coords(1,0), Coords(0,1)]
        # Get the horizontal and vertical size of the direction
        sizes = [self.rect.size(d) for d in directions]
        ds = zip(directions, sizes)
        direction, size = random.choices(ds, sizes)[0]
        index = random.randrange(size)
        return index, direction

def find_coord(subrooms, roots, coord):
    """Find which leaf subroom has the given coord."""
    curr_roots = roots
    while True:
        candidates = [r for r in curr_roots if subrooms[r].rect.coord_within(coord)]
        assert len(candidates) == 1
        candidate = candidates[0]
        if candidate.is_leaf():
            break
        else:
            curr_roots = candidate.children
    return candidate

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
        g.add_node(leaf.id)
        for o in leaf.obstacles:
            g.add_node(o[0], data=(o[2]))
        g.add_edge(leaf.id, o[0])
        g.add_edge(o[0], leaf.id)
    # Once all the subrooms have been added, produce the adjacencies
    for leaf in subroom_leaves:
        for neighbor_adj in leaf.adj:
           g.add_edge(leaf.id, neighbor_adj[0], data=(neighbor_adj[1], neighbor_adj[2]))
    return g

def embed_room_graph(room_graph, subroom_graph):
    """Embed the room graph into the subroom graph, resulting in a new graph
    which is the graph that will actually be searched over during subroom generation."""
    # Key - subroom_id, value - list of nodes belonging to that subroom
    # Used to create a subgraph when building the subroom
    subroom_nodes = collections.defaultdict(list)
    # The subrooms which the graph embedding actually uses
    # Used to calculate the subrooms which are completely unused.
    used_subrooms = set()
    entrances = []
    g = basicgraph.BasicGraph()
    for node1, node2 in room_graph.get_edges():
        itemset = room_graph.get_edge_data(node1, node2)
        #TODO: randomized DFS?
        path = basicgraph.bfs_path(subroom_graph.DFS(node1, node2))
        current_node = None
        for first, second in zip(path, path[1:]):
            if first in room_graph:
                # First is an obstacle node
                # Copy the data: the rectangle of actual tiles that this obstacle represents
                #TODO: might only want the last two entries: the target squares
                if first not in g:
                    g.add_node(first, data=subroom_graph.get_data[first])
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
                    e1, e2 = choose_entrances(edge_fs, edge_sf)
                    # Create a node in the first subroom
                    g.add_node(fs_name, data=e1)
                    subroom_nodes[first].append(fs_name)
                    used_subrooms.add(first)
                    # Create a node in the second subroom
                    g.add_node(sf_name, data=e2)
                    subroon_nodes[second].append(sf_name)
                    used_subrooms.add(second)
                    # Add the entrance to the list of entrances to be used
                    # to fill them with air
                    entrances.append(e1)
                    entrances.append(e2)
                # Regardless of what type of node, connect them up
                # TODO: update edge append instead!
                g.add_edge(current_node, fs_name, data=itemset)
                g.add_edge(fs_name, sf_name, data=itemset)
                current_node = fs_name
    return g, subroom_nodes, used_subrooms, entrances

def choose_entrances(adj1, adj2):
    """Choose where on an adjacency to make an entrance."""
    # Make sure the two adjacencies are in opposite directions
    assert adj1[2] == adj2[2].neg()
    # The long axis of the adjacency is perpendicular to its direction
    direction = adj1[2].abs()
    axis = Coord(1,1) - direction
    # Find the length of each adjacency
    adj1_size = adj1[1].size(axis)
    adj2_size = adj2[1].size(axis)
    assert adj1_size == adj2_size
    #TODO: entrances to morph subrooms can be as small as 1...
    #PARAM
    entrance_size = random.randrange(3,7)
    entrance_placement = random.randrange(adj1_size - entrance_size)
    # Compute the entrances
    entrance1_start = adj1[0] + axis.scale(entrance_placement)
    entrance2_end = entrance1_start + axis.scale(entrance_size) + direction
    # Entrance2 is just shifted by one in the direction that adj1 faces
    entrance2_start = entrance1_start + adj1[2]
    entrance2_end = entrance1_end + adj1[2]
    return Rect(entrance1_start, entrance1_end), Rect(entrance2_start, entrance2_end)

def make_subroom_walls(level, subroom_leaves):
    for leaf in subroom_leaves:
        for a in leaf.adj:
            room_utils.mk_default_rect(level, a[1])

def subroom_partition(room, max_parts, min_partsize, obstacles):
    """Creates a partition of the room into subrooms."""
    # First, generate a greedy rectangularization of the concrete map for the room
    current_id, roots, subrooms = rectangularize(room.cmap, obstacles)
    while True:
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
        if current_node.check_valid(index, direction):
            id1 = current_id
            current_id += 1
            id2 = current_id
            current_id += 1
            current_node.subdivide(index, direction, id1, id2)
        else:
            break
    return roots, subrooms

#TODO: parameterized by direction in both x and y
def rectangularize(cmap, obstacles):
    subrooms = {}
    # Stores the set of CMAP tiles for each subroom
    subroom_sets = {}
    roots = []
    current_id = 0
    # sorts topmost leftmost
    positions = sorted(cmap.keys())
    # Find rectangles until the entire cmap is covered
    while len(positions) > 0:
        pos = positions[0]
        rect = find_rect(cmap, pos)
        for c in rect.as_list():
            positions.remove(c)
        # Add it to the subroom tree, and convert its size and position into the level format
        subrooms[current_id] = SubroomNode(current_id, rect.scale(16), [], [])
        subroom_rects[current_id] = coord.xy_set(pos, rect)
        roots.append(current_id)
        current_id += 1
    # Find adjacencies between the rectangles
    for r1, r2 in itertools.combinations(roots, 2):
        # Since positions was sorted and the combinations function
        # outputs tuples in sorted order, r_1 is above / to the left of r_2
        r1_adj, r2_adj = find_adjacency(subroom_sets[r1], subroom_sets[r2])
        subrooms[r1].adj.extend(r1_adj)
        subrooms[r2].adj.extend(r2_adj)
    # Assign the obstacles
    for o in obstacles:
        done = False
        for s in subrooms.values():
            # If the object is contained by the subroom...
            if o[1].within(s.rect):
                s.obstacles.append(o)
                done = True
                break
        if not done:
            assert False, "Obstacle not contained by a single subroom: " + str(o)
    return current_id, roots, subrooms

def find_adjacency(r1, r2):
    # D R L U
    directions = [Coord(0,1), Coord(1,0), Coord(-1,0), Coord(0,-1)]
    for d in directions:
        neighbors = sorted([p + d for p in r1 if p + d not in r1 and p + d in r2])
        if len(neighbors > 0):
            # Topmost leftmost neighbor
            start = neighbors[0]
            dist = 16 * len(neighbors)
            border2_start = start.scale(16)
            #TODO can be cleaned up with d.abs()?
            if d < Coord(0,0):
                border2_start += d.scale(-15)
                dist_coords = (Coord(1,1) + d).scale(dist)
                border2_end = border2_start + dist_coords - d
            else:
                dist_coords = (Coord(1, 1) - d).scale(dist)
                border2_end = border2_start + dist_coords + d
            border1_start = border2_start - d
            border1_end = border2_end - d
            r1 = Rect(border1_start, border1_end)
            r2 = Rect(border2_start, border2_end)
            return [(r2.id, r1, d)], [(r1.id, r2, d.neg())]
        # No borders
        return [], []

def find_rect(cmap, pos):
    """Find the largest rectangle that will fit into the given cmap at the given pos."""
    assert pos in cmap
    best_rect = Rect(pos, pos + Coord(1,1))
    # Find the largest x and y that we need to check for a rectangle
    xmax = 0
    while True:
        c = pos + Coord(xmax, 0)
        if c in cmap:
            xmax += 1
    ymax = 0
    while True:
        c = pos + Coord(0, ymax)
        if c in cmap:
            ymax += 1
    max_rect = Rect(pos, pos + Coord(xmax, ymax))
    max_area = 1
    for c in max_rect.as_list:
        c = Coord(x, y)
        # If the bottom right corner is in the map, then it's a valid rectangle
        if pos + c in cmap:
            r = Rect(pos, c + Coord(1,1))
            area = r.area()
            # If it's bigger than the current best rectangle, replace the current best
            if area > max_area:
                best_rect = r
                max_area = area
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
