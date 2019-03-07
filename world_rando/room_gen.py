from .room_dtypes import *
from .room_utils import *
from .coord import *
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
# Tile rooms is Coord -> room#,
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
            gstart.add_node(start)
        gend = rooms[room_end].graph
        if end not in gend.nodes:
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

class SubroomNode(object):

    def __init__(self, id, rect, adjacencies, obstacles):
        self.id = id
        self.rect = rect
        self.adj = adjacencies
        self.obstacles = obstacles
        self.children = []

    # an adjacency is a 4-tuple of (id, rect_start, rect_end, direction)
    # an obstacle is a 5-tuple of (name, obstacle_start, obstacle_end, target_start, target_end)
    def subdivide(self, index, direction, id1, id2, subrooms):
        """Divide a room at index in the given direction. Cutting a room in the x-direction
        means that the horizontal axis of the room is divided by the cut. Coords of the room
        /before/ index will belong to the first part, while coords of the room at or after index
        will belong to the second part."""
        self.check_inbounds(index, direction)
        # Compute the rectangles that each child will take up
        rect1, rect2 = coord.split_rect(self.rect, index, direction)
        # Compute the adjacencies that each child will have
        #TODO: might be able to get rid of the first ifelse since the left/top adjacencies will end
        # before index
        adj1 = []
        adj2 = []
        for a in self.adjacencies:
            # The other SubroomNode implicated in this adjacency
            other = subrooms[a[0]]
            # child1 takes left/top adjacencies
            if a[3] == direction.neg():
                adj1.append(a)
                # Reassign the old ajdancency for the neighbor
                other.reassign_adj(self.id, id1)
            # child2 takes right/bottom adjacencies
            if a[3] == direction:
                adj2.append(a)
                other.reassign_adj(self.id, id2)
            else:
                # If it ends before the index, it belongs to child1
                if a[2].index(direction) < index:
                    adj1.append(a)
                    other.reassign_adj(self.id, id1)
                # If it starts after the index, it belongs to child2
                elif a[1].index(direction) > index:
                    adj1.append(a)
                    other.reassign_adj(self.id, id2)
                # If neither, it must be split
                else:
                    ar1, ar2 = coord.split_rect((a[1], a[2]), index, direction)
                    a1 = (a[0], ar1[0], ar1[1], a[3])
                    a2 = (a[0], ar2[0], ar2[1], a[3])
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
            if o[2].index(direction) < index:
                obs1.append(o)
            elif o[1].index(direction) > index:
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
        new_r1, new_r2 = coord.split_rect((adj[0], adj[1]), index, direction)
        new_1 = (id1, new_r1[0], new_r1[1], adj[3])
        new_2 = (id2, new_r2[0], new_r2[1], adj[3])
        self.adj = [i for i in other.adj if i[0] != old_id] + [new_1, new_2]

    def div_point(self, index, direction):
        return self.rect[0] + direction.scale(index)

    def obv_point(self, index, direction):
        return self.div_point() + (Coord(1,1) - d) * self.rect[1]

    def size(self):
        """Returns the total number of places a cut could be made in self."""
        return self.range[1].x - self.range[0].x + self.range[1].y - self.range[1].y

    def as_set(self):
        return xy_set(self.rect[0], self.rect[1])

    def check_inbounds(index, direction):
        """Check that the proposed cut is in-bounds."""
        div_point = self.div_point()
        dp = div_point.index(direction)
        startpoint = self.rect[0].index(direction)
        endpoint = self.rect[1].index(direction)
        assert dp < endpoint and dp >= startpoint

    def check_valid(index, direction, min_size)
        """Checks that a cut can be made at the given index in the given direction
        if the smallest size of a subroom is min_size. Fails with assertion if the
        cut is outside of range, returns False if the cut is within range but would
        result in a room that is too small."""
        self.check_inbounds(index, direction)
        #TODO: kind of wasteful to compute these things again...
        div_point = self.div_point(index, direction)
        obv_point = self.obv_point(index, direction)
        dp = div_point.index(direction)
        startpoint = self.rect[0].index(direction)
        endpoint = self.rect[1].index(direction)
        if dp - startpoint < min_size:
            return False
        if endpoint - dp < min_size:
            return False
        # a 2xX rectangle indicating where the walls of the proposed cut will appear
        cut_rect = (div_point - d, obv_point + d)
        cut_set = coord.xy_set(cut_rect[0], cut_rect[1])
        # Check obstacles:
        for o in self.obstacles:
            o_set = coord.xy_set(o[1], o[2])
            # Slow but easy way to check rectangle intersection
            if len(o_set & cut_set) > 0:
                return False
        return True

    def choose_cut(self):
        """Randomly choose a possible cut."""
        directions = [Coords(1,0), Coords(0,1)]
        # Get the horizontal and vertical size of the direction
        sizes = [self.rect[1].index(d) - self.rect[0].index(d) for d in directions]
        ds = zip(directions, sizes)
        direction, size = random.choices(ds, sizes)[0]
        index = random.randrange(size)
        return index, direction

def find_leaves(subrooms, roots):
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
    # Add a node for each subroom and each obstacle
    for leaf in subroom_leaves:
        g.add_node(leaf.id)
        for o in leaf.obstacles:
            g.add_node(o[0], data=(o[3], o[4]))
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
    # key - subroom_id, value - list of nodes belonging to that subroom

    subroom_nodes = collections.defaultdict(list)
    unused_subrooms = set()
    used_subrooms = set()
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
                # TODO: pick a subset of the tiles to use as an exit!
                if fs_name not in g:
                    g.add_node(fs_name, data=edge_fs)
                    subroom_nodes[first].append(fs_name)
                    used_subrooms.add(first)
                if sf_name not in g:
                    g.add_node(sf_name, data=edge_sf)
                    subroon_nodes[second].append(sf_name)
                    used_subrooms.add(second)
                # Connect them up
                g.add_edge(current_node, fs_name, data=itemset)
                g.add_edge(fs_name, sf_name, data=itemset)
                current_node = fs_name
    #TODO: calculate unused_subrooms!
    return g, subroom_nodes, unused_subrooms

def make_subroom_walls(level, subroom_leaves):
    for leaf in subroom_leaves:
        for a in leaf.adj:
            room_utils.mk_default_rect(level, a[1], a[2])

def miniroom_partition(room, max_parts, min_partsize, obstacles):
    """Creates a partition of the room into minirooms."""
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
    #TODO
    pass

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
        for x in range(pos.x, rect.x):
            for y in range(pos.y, rect.y):
                positions.remove(coord.y)
        # Add it to the subroom tree, and convert its size and position into the level format
        subrooms[current_id] = SubroomNode(current_id, (pos.scale(16), rect.scale(16)), [], [])
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
        o_set = coord.xy_set(o[1], o[2])
        for r, s in subroom_sets.items():
            if o_set <= s:
                r.obstacles.append(o)
                # Break since the s are disjoint
                break
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
            return [(r2.id, border1_start, border1_end, d)], [(r1.id, border2_start, border2_end, d.neg())]
        # No borders
        return [], []

def find_rect(cmap, pos):
    """Find the largest rectangle that will fit into the given cmap at the given pos."""
    assert pos in cmap
    best_rect = pos + Coord(1,1)
    max_area = 1
    x = pos.x + 1
    y = pos.y + 1
    while True:
        while True:
            c = Coord(x, y)
            if pos + c in cmap:
                area = (c - pos).area()
                if area > max_area:
                    best_rect = c
                    max_area = area
            else:
                break
            x += 1
        x = 0
        y += 1
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
            hflip = (level1 >> 10) & 1
            vflip = (level1 >> 11) & 1
            tindex = level1 & 0b1111111111
            texture = Texture(tindex, (hflip, vflip))
            tiletype = Type(ttype, bts)
            level[Coord(x,y)] = Tile(texture, tiletype)
    return level
