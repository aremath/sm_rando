import itertools
import random
import collections
from collections import OrderedDict

from sm_rando.data_types import basicgraph
from sm_rando.world_rando.room_dtypes import Room, Level, Tile, Texture, Type
from sm_rando.world_rando.room_utils import mk_default_rect, mk_air_rect
from sm_rando.world_rando.coord import Coord, Rect
from sm_rando.world_rando.util import weighted_random_order

from sm_rando.world_rando.room_dtypes import *
from sm_rando.world_rando.room_utils import *
from sm_rando.world_rando.coord import *
from sm_rando.world_rando.util import *

from sm_rando.world_rando.concrete_map import bfs, bfs_partition

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
    rooms = OrderedDict()
    for room_id, coord_set in room_tiles.items():
        room_bbox = extent(coord_set)
        room_cmap, room_pos = cmap.sub(room_bbox, relative=True)
        rooms[room_id] = Room(room_cmap, room_bbox.size_coord(), room_id, room_pos)
    return rooms

#TODO: work in progress
# Tile rooms is Coord -> room id,
# paths is [(start_node, end_node, [MCoord])]
# rooms is room_id -> room
#TODO: Generate "master room graph" then use sub to create room graphs
def room_graphs(rooms, tile_rooms, paths):
    #TODO: node_locs for each node and each door node.
    # room_node_locs: room_id -> node -> Coord
    for (start, end, path, items) in paths:
        room_start = tile_rooms[path[0]]
        room_end = tile_rooms[path[-1]]
        # Add nodes for the items at the start and end of this path
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
        # Travel along the path, creating the necessary doors
        for new_pos in path:
            new_room = tile_rooms[new_pos]
            if new_room != current_room:
                gcurrent = rooms[current_room].graph
                gnew = rooms[new_room].graph
                # Create a door node in the old room
                current_wr = current_pos.wall_relate(new_pos)
                current_door = str(current_room) + "_" + str(current_pos) + "_" + current_wr
                if current_door not in gcurrent.nodes:
                    gcurrent.add_node(current_door)
                    # Create a new door for current -> new
                    d = rooms[current_room].doors
                    d.append(Door(current_pos, current_wr, current_room, new_room, len(d), current_door))
                # Link the current node with the door
                gcurrent.update_edge(current_node, current_door, items)
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
        # Link the final current node with end
        gend.update_edge(current_node, end, items)

def make_rooms(room_tiles, cmap, paths, settings, patterns):
    rooms = room_setup(room_tiles, cmap)
    tile_rooms = reverse_list_dict(room_tiles)
    room_graphs(rooms, tile_rooms, paths)
    # ... generate map data etc ...
    for i, r in rooms.items():
        print("BEGIN: Generating room " + str(i))
        r.level = level_of_cmap(r)
        make_subrooms(r, settings, patterns)
        # ...
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
                pattern_rect = Rect(Coord(0,0), pattern.dimensions)
                rel_obstacle = rel_obstacle_r.flip_in_rect(pattern_rect, Coord(1,0))
                rel_target = rel_target_r.flip_in_rect(pattern_rect, Coord(1,0))
                rel_item_placement = rel_item_placement_r.flip_in_rect(pattern_rect, Coord(1,0))
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

#TODO: instead of constantly CHANGING adjacencies, simply create NEW, smaller adjacencies
# between lower elements of the subroom tree.
def make_subrooms(room, settings, patterns):
    """
    Create the subrooms for a room
    """
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
    min_entrance_size = settings["min_room_entrance_size"]
    max_entrance_size = settings["max_room_entrance_size"]
    subroom_graph = subroom_adjacency_graph(subroom_leaves, min_entrance_size, max_entrance_size)
    #subroom_graph.visualize("./output/room" + str(room.room_id) + "subroom_graph")
    print("Embedding room graph")
    t = embed_room_graph(room.graph, subroom_graph)
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

class SubroomState(object):
    """Manages the creation / deletion of subrooms and the subroom graph"""

    def __init__(self, start_subroom, walls):
        #TODO: how to represent cross-room adjacencies?
        self.subroom_id_counter = 0
        self.recycle_ids = []
        self.walls = walls
        self.obstacles = obstacles
        self.g = basicgraph.BasicGraph()
        self.new_subroom(start_subroom)
        #TODO: check borderedness of the starting subroom?
        # -> only need to do one check since borderedness is invariant under split, merge

    def get_new_id(self):
        if len(self.recycle_ids == 0):
            new_id = self.subroom_id_counter
            self.subroom_id_counter += 1
            return new_id
        else:
            return self.recycle_ids.pop()

    def delete_subroom(self, sid):
        for _, n in self.g.get_edges(sid):
            assert not self.g.is_edge(n, sid), "Cannot delete while an edge exists"
        self.g.remove_node(sid)
        self.recycle_ids.append(sid)

    def new_subroom(self, subroom):
        sid = self.get_new_id()
        self.g.add_node(sid, data=subroom)
        return sid

    def delete_adjacency(self, s1, s2):
        adj = self.g[(s1, s2)]
        self.g.remove_edge(sid, n)
        self.g.remove_edge(n, sid)
        return adj

    def new_adjacency(self, s1, s2, adj):
        self.g.add_edge(s1, s2, data=adj)
        self.g.add_edge(s2, s1, data=adj)

    #TODO: add and remove obstacles (ensuring obstacles and targets are within subrooms)

    #TODO: Allow specification of required subroom size
    #TODO: then have check-valid
    def split_subroom(self, sid, adj):
        # First ensure that the proposed adj doesn't break any obstacles
        for o in self.obstacles:
            i = (o.target_set | o.obstacle_set) & adj.tiles
            if len(i) != 0:
                assert False, "Proposed adjacency hits obstacle"
        # Find the tiles for the new subrooms
        s_tiles = self.g[sid].tiles
        # The tiles that make up both subrooms
        new_tiles = s_tiles - adj.tiles
        assert len(new_tiles) > 0
        # Arbitrary element to be the root
        s1_root = next(iter(new_tiles))
        _, s1_tiles = bfs(new_tiles, s1_root)
        not_s1_tiles = new_tiles - s1_tiles
        assert len(s2_tiles) > 0
        # Arbitrary element to be the root
        s2_root = next(iter(not_s1_tiles))
        _, s2_tiles = bfs(new_tiles, s2_root)
        # Check that all tiles are accounted for
        assert s1_tiles | s2_tiles == new_tiles
        # Check that no tiles are double counted
        assert len(s1_tiles & s2_tiles) == 0
        # Create the new subrooms
        sid1 = self.new_subroom(s1_tiles)
        sid2 = self.new_subroom(s2_tiles)
        self.new_adjacency(sid1, sid2, adj)
        # For all subrooms that used to border sid,
        # Update old adjacencies by creating new edges
        for n in self.g.neighbors(sid):
            # Delete the old edges
            adj = self.delete_adjacency(sid, n)
            adj_border = adj.border()
            border1 = adj_border & s1_tiles
            border2 = adj_border & s2_tiles
            assert len(border1 & border2) == 0, "Non-disjoint border pair"
            # Split old adjacency if it borders both subrooms
            # Split the old adjacency by partitioning it with a "growing partition"
            # where the priority of cells to grab depends on average distance to the other border
            if len(border1) != 0 and len(border2) != 0:
                t = adj.tiles
                b1_root = next(iter(border1))
                b2_root = next(iter(border2))
                priority1 = lambda p: sum([euclidean(p, c) for c in border2])
                priority2 = lambda p: sum([euclidean(p, c) for c in border1])
                priorities = {b1_root: priority1, b2_root: priority2}
                meansets = {b1_root: border1, b2_root: border2}
                _, f = bfs_partition(t, [b1_root, b2_root], meansets, priorities)
                adj1 = Adjacency(f[b1_root])
                adj2 = Adjacency(f[b2_root])
                self.new_adjacency(n, sid1, adj1)
                self.new_adjacnecy(n, sid2, adj2)
            # If it only borders one, update the ID
            else:
                elif len(border1) != 0:
                    b = sid1
                elif len(border2) != 0:
                    b = sid2
                else:
                    assert False, "Edge without border"
                self.new_adjacency(n, b, adj)
        # Delete the old subroom
        self.delete_subroom(sid)

    def merge_subrooms(self, sid1, sid2):
        # Create a new subroom with a new id that has the union of the two subrooms
        # and their corresponding adjacency in tiles
        adj = self.delete_adjacency(sid1, sid2)
        new_tiles = self.g[sid1].tiles | self.g[sid2].tiles | adj.tiles
        sid = self.new_subroom(new_tiles)
        # Update existing adjacencies
        n1 = set(self.g.neighbors(sid1))
        n2 = set(self.g.neighbors(sid2))
        for n in n1 | n2:
            # Need to merge adjacency (union) if one subroom borders both sid1 and sid2
            if n in n1 and n in n2:
                adj1 = self.delete_adjacency(sid1, n)
                adj2 = self.delete_adjacency(sid2, n)
                new_adj = Adjacency(adj1.tiles | adj2.tiles)
                self.new_adjacency(sid, n, new_adj)
            else:
                elif n in n1:
                    new_adj = self.delete_adjacency(sid1, n)
                elif n in n2:
                    new_adj = self.delete_adjacency(sid2, n)
                self.new_adjacency(sid, n, new_adj)
        # If not, need to update the ID
        # Delete the old subrooms
        self.delete_subroom(sid1)
        self.delete_subroom(sid2)

def coord_set_border(s):
    directions = [Coord(0,1), Coord(1,0), Coord(-1,0), Coord(0,-1)]
    border = sorted([p + d for p in s for d in directions if p + d not in s])

# A subroom is a contiguous set of tiles which is surrounded by walls or adjacencies
# An adjacency is a set of tiles (not necessarily contiguous) which is required to traverse in order
# to travel from subroom A to subroom B

class Subroom(object):
    """A subroom is a contiguous set of tiles which is surrounded by
    wall tiles or adjacency tiles"""

    def __init__(self, sid, tiles):
        self.tiles = tiles

    # The bounding box of the tiles
    def frame(self):
        #TODO
        pass

    # Tuple of minimum x-extent, minimum y-extent
    def size(self):
        #TODO
        pass

    def border(self):
        return coord_set_border(self.tiles)

class Adjacency(object):
    """An adjacency is a set of tiles (may not be contiguous) which must be traversed to get
    between a pair of subrooms."""

    def __init__(self, tiles):
        self.tiles = tiles

    def border(self):
        return coord_set_border(self.tiles)
    #TODO: use patterns to check if an adjacency is usable at all

#TODO: image DSL for obstacles
class Obstacle(object):

    def __init__(self, name, obstacle_rect, target_rect):
        self.name = name
        self.obstacle_set = obstacle_rect.as_set()
        self.target_set = target_rect.as_set()

#TODO: implement as a method of Subroom. Useful for strategies
#    def choose_cut(self):
#        """Randomly choose a possible cut."""
#        directions = [Coord(1,0), Coord(0,1)]
#        # Get the horizontal and vertical size of the direction
#        sizes = [self.rect.size(d) for d in directions]
#        ds = list(zip(directions, sizes))
#        direction, size = random.choices(ds, sizes)[0]
#        index = random.randrange(size)
#        return index, direction

#TODO: Some way to determine the subroom that houses a given obstacle for graphs
#def find_coord(subrooms, roots, coord):
#    """Find which leaf subroom has the given coord."""
#    curr_roots = roots
#    while True:
#        candidates = [r for r in curr_roots if subrooms[r].rect.coord_within(coord)]
#        assert len(candidates) == 1
#        candidate_id = candidates[0]
#        candidate = subrooms[candidate_id]
#        if candidate.is_leaf():
#            break
#        else:
#            curr_roots = candidate.children
#    return candidate_id

#TODO: with update, need patterns to do this properly
# Should check whether each edge allows 
#def subroom_adjacency_graph(subroom_leaves, min_entrance_size, max_entrance_size):
#    g = basicgraph.BasicGraph()
#    # Add a node for each subroom and each obstacle that holds the target region of the obstacle
#    for leaf in subroom_leaves:
#        leaf_name = str(leaf.id)
#        g.add_node(leaf_name)
#        # Add an edge between each obstacle and the leaf that contains it.
#        for o in leaf.obstacles:
#            g.add_node(o.name, data=o)
#            g.add_edge(leaf_name, o.name)
#            g.add_edge(o.name, leaf_name)
#    # Once all the subrooms have been added, produce the adjacencies
#    for leaf in subroom_leaves:
#        for neighbor_adj in leaf.adj:
#            # Only add an edge of the adjacency is enterable
#            if neighbor_adj.can_enter(min_entrance_size):
#                # Add a tentative entrance and an edge
#                if neighbor_adj.entrance is None:
#                    neighbor_adj.add_entrance(min_entrance_size, max_entrance_size)
#                leaf_name = str(leaf.id)
#                other_name = str(neighbor_adj.get_other_id(leaf.id))
#                g.add_edge(leaf_name, other_name, data=neighbor_adj)
#    return g

#TODO:
#def embed_room_graph(room_graph, subroom_graph):
#    """
#    Embed the room graph into the subroom graph, resulting in a new graph
#    which is the graph that will actually be searched over during subroom generation.
#    """
#    # Key - subroom_id, value - list of nodes belonging to that subroom
#    # Used to create a subgraph when building the subroom
#    subroom_nodes = collections.defaultdict(list)
#    # The subrooms which the graph embedding actually uses
#    # Used to calculate the subrooms which are completely unused.
#    used_subrooms = set()
#    g = basicgraph.BasicGraph()
#    for node1, node2 in room_graph.get_edges():
#        itemset = room_graph.get_edge_data(node1, node2)
#        #TODO: randomized DFS?
#        finished, offers = subroom_graph.DFS(node1, node2)
#        path = basicgraph.bfs_path(offers, node1, node2)
#        current_node = None
#        for first, second in zip(path, path[1:]):
#            if first in room_graph:
#                # First is an obstacle node
#                # Copy the data: the rectangle of actual tiles that this obstacle represents
#                #TODO: might only want the target squares
#                if first not in g:
#                    g.add_node(first, data=subroom_graph.nodes[first].data)
#                current_node = first
#            elif second in room_graph:
#                # Second is an obstacle node
#                if second not in g:
#                    g.add_node(second, data=subroom_graph.get_data[second])
#                current_node = second
#            else:
#                # edge between two subroom nodes
#                edge_fs = subroom_graph.get_edge_data(first, second)
#                edge_sf = subroom_graph.get_edge_data(second, first)
#                fs_name = str(first) + "-" + str(second)
#                sf_name = str(second) + "-" + str(first)
#                # Add a node for the exit to the old subroom and the entrance to the new one
#                if fs_name not in g:
#                    # Subroom interface nodes should only be added two at a time
#                    assert sf_name not in g
#                    # Choose a place to break the wall between the two subrooms
#                    #TODO: Decide the type of each entrance based on what items are available
#                    e = edge_fs.entrance
#                    edge_fs.crossings.append(itemset)
#                    # Create a node in the first subroom
#                    g.add_node(fs_name, data=e)
#                    subroom_nodes[first].append(fs_name)
#                    used_subrooms.add(first)
#                    # Create a node in the second subroom
#                    g.add_node(sf_name, data=e)
#                    subroom_nodes[second].append(sf_name)
#                    used_subrooms.add(second)
#                # Regardless of what type of node, connect them up
#                # TODO: update edge append instead!
#                g.add_edge_append(current_node, fs_name, data=itemset)
#                g.add_edge_append(fs_name, sf_name, data=itemset)
#                current_node = fs_name
#    return g, subroom_nodes, used_subrooms

#TODO 
#def make_subroom_walls(level, subroom_leaves):
#    """
#    Make the walls for each subroom
#    """
#    for leaf in subroom_leaves:
#        for a in leaf.adj:
#            a.mk_wall(level)

#TODO
#def print_subrooms(subrooms):
#    """
#    Print the subrooms nicely
#    """
#    for s1 in subrooms.values():
#        if s1.is_leaf():
#            print("{} : {}".format(s1.id, s1.rect))
#            for a in s1.adj:
#                print("\t {} , {}, {}, d{}".format(a.id1, a.id2, a.rect, a.direction))

#TODO: Update this to use SubroomState rather than SubroomNode
#TODO: Include a way to use "strategies" sequentially
# "strategy" is a method for creating a finite sequence of split()s and merge()s
# -> implement "rectangularize(subroom_state, room.cmap)
#TODO: some way to create the initial state, including room walls (use search?)
#TODO: "linear" split() which randomly determines an index to split on

# Contintue to partition until EACH subroom fails a partition (because it is too small,
# or intersects an obstacle)
def subroom_partition(room, max_parts, min_partsize, obstacles):
    """
    Creates a partition of the room into subrooms
    Respects that obstacles (such as doors) must be fully within a subroom
    """
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

#TODO: use split()ing to make this code much easier to read
#TODO: parameterized by direction in both x and y
# i.e. which corner to start from.
def rectangularize(cmap, obstacles):
    """
    Finds a set of initial rectangular subrooms for the given concrete map
    """
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
    # Assign the obstacles to their respective subrooms
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
    """
    Adds an adjacency between two subrooms if their sets of contained regions border each other
    """
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
            directions = {}
            directions[r2.id] = d
            directions[r1.id] = -d
            a = Adjacency(r1.id, r2.id, rect, directions)
            r1.adj.append(a)
            r2.adj.append(a)
            return
        # They do not border each other
        else:
            pass

#TODO: this is less efficient than search-based methods.
#TODO: Expand the rectangle to the right first in order to get more horizontal rooms
def find_rect(positions, pos):
    """
    Finds biggest rectangle that fits at pos for a given set of map positions that
    the rectangle may occupy. Expands the rectangle down and to the right.
    """
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
    assert levelsize % 2 == 0, "Purported level size {} is not even!".format(levelsize)
    assert levelsize == dimensions.x * dimensions.y * 2, "Level data length {} does not match specified room dimensions {}".format(levelsize, dimensions.x * dimensions.y * 2)
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

