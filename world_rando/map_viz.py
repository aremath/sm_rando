# visualizes a concrete map of the form laid out in concrete_map.py
from collections import defaultdict
from itertools import tee
from functools import reduce
from PIL import Image
import numpy as np
import cv2
from math import pi
from world_rando.concrete_map import *
from world_rando.map_gen import Path

def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

#TODO: use path to find the files?
def load_map_tiles(map_dir):
    i0w  = Image.open(map_dir + "/0wall.png")
    i1w  = Image.open(map_dir + "/1wall.png")
    i2w  = Image.open(map_dir + "/2wall.png")
    i2wp = Image.open(map_dir + "/2wallpipe.png")
    i3w  = Image.open(map_dir + "/3wall.png")
    i4w  = Image.open(map_dir + "/4wall.png")
    ba   = Image.open(map_dir + "/blank_alpha.png")
    ia   = Image.open(map_dir + "/item_alpha.png")
    ea   = Image.open(map_dir + "/is_elevator.png")
    et   = Image.open(map_dir + "/elevator.png")
    wall_dict = {"0w" : i0w,
                 "1w" : i1w,
                 "2w" : i2w,
                 "2wp": i2wp,
                 "3w" : i3w,
                 "4w" : i4w,
                 "et" : et,
                 "b"  : ba
                }
    return wall_dict, ba, ia, ea

def find_image(walls, xy):
    """returns which image to use, and how to rotate it"""
    nwalls = len(walls)
    # unoptimized spaghetti code
    if nwalls == 0:
        return "0w", 0
    elif nwalls == 1:
        if Coord(-1,0) in walls:
            return "1w", 0
        if Coord(0,-1) in walls:
            return "1w", 270
        if Coord(1,0) in walls:
            return "1w", 180
        if Coord(0,1) in walls:
            return "1w", 90
    elif nwalls == 2:
        if Coord(0,1) in walls and Coord(0,-1) in walls:
            return "2wp", 90
        if Coord(-1,0) in walls and Coord(1,0) in walls:
            return "2wp", 0
        if Coord(-1,0) in walls and Coord(0,-1) in walls:
            return "2w", 0
        if Coord(0,-1) in walls and Coord(1,0) in walls:
            return "2w", 270
        if Coord(1,0) in walls and Coord(0,1) in walls:
            return "2w", 180
        if Coord(0,1) in walls and Coord(-1,0) in walls:
            return "2w", 90
    elif nwalls == 3:
        if Coord(1,0) not in walls:
            return "3w", 0
        if Coord(0,1) not in walls:
            return "3w", 270
        if Coord(-1,0) not in walls:
            return "3w", 180
        if Coord(0,-1) not in walls:
            return "3w", 90
    elif nwalls == 4:
        return "4w", 0
    assert False, "no matching walls! " + str(walls)
       
def map_viz(rcmap, filename, map_dir):
    map_extent = rcmap.map_extent()
    map_size = map_extent.size_coord()
    map_image = Image.new("RGBA", ((map_size.x)*16, (map_size.y)*16), "black")
    # bind the current region for easy re-use
    wmap, blank, item, elevator = load_map_tiles(map_dir)
    for c in map_extent.as_list():
        c_rel = c - map_extent.start
        image_loc = (c_rel.x*16, c_rel.y*16)
        if c in rcmap:
            mtile = rcmap[c]
            if mtile.tile_type == TileType.elevator_shaft:
                image_name, rotation = "et", 0
            elif mtile.tile_type == TileType.blank:
                image_name, rotation = "b", 0
            else:
                image_name, rotation = find_image(mtile.walls, c)
            image = wmap[image_name]
            imrotate = image.rotate(rotation)
            map_image.paste(imrotate, image_loc, imrotate)
            if mtile.is_item:
                map_image.paste(item, image_loc, item)
            if (mtile.tile_type == TileType.elevator_main_up or
                mtile.tile_type == TileType.elevator_main_down):
                map_image.paste(elevator, image_loc, elevator)
        else:
            # it's a blank
            map_image.paste(blank, image_loc, blank)
    map_image.save(filename)
    return map_image

def gen_cases(lrep):
    """take a pattern-matching TF line and generate the cases"""
    if len(lrep) == 1:
        if lrep[0] == "T":
            return [[True]]
        elif lrep[0] == "F":
            return [[False]]
        else:
            return [[True], [False]]
    if lrep[0] == "T":
        return map(lambda l: [True] + l[:], gen_cases(lrep[1:]))
    elif lrep[0] == "F":
        return map(lambda l: [False] + l[:], gen_cases(lrep[1:])) #TODO: do I need this copy?
    elif lrep[0] == "_":
        c1 = map(lambda l: [True] + l[:], gen_cases(lrep[1:])) #TODO: do I need this copy?
        c2 = map(lambda l: [False] + l[:], gen_cases(lrep[1:])) #TODO: do I need this copy?
        return list(c1) + list(c2)
    else:
        assert False, lrep

def tiles_parse(tile_file):
    """Creates a simple boolean pattern matching dictionary.
    out is a dict where key = a tuple of bools specifying what type of tile
    and value = a tuple of (vflip, hflip, tile index) or None if there is no matching tile."""
    out = {}
    f = open(tile_file, "r")
    # first, reverse the readlines so newer things are applied last
    ls = f.readlines()[::-1]
    for line in ls:
        if len(line) == 0:
            continue
        elif line[0] == "#":
            continue
        else:
            line =  line.strip()
            line = line.split()
            if len(line) == 0:
                continue
            if line[-1] == "ERROR":
                val = None
                lrep = line[:-1]
            else:
                ints = map(lambda x: int(x, 16), line[-3:])
                val = tuple(ints)
                lrep = line[:-3]
            cases = gen_cases(lrep)
            keys = map(lambda l: tuple(l), cases)
            for k in keys:
                out[k] = val
    return out

#TODO: use tile_type more effectively!
def cmap_to_tuples(cmap, tile_mapping):
    """ create an dict of key - xy, value - (hflip, vflip, index) from a cmap for that area"""
    cmap_tuples = {}
    for mc, tile in cmap.items():
        xy = (mc.x, mc.y)
        is_e_arrow = (tile.tile_type == TileType.up_arrow or tile.tile_type == TileType.down_arrow)
        is_e_shaft = (tile.tile_type == TileType.elevator_shaft)
        is_e_main  = (tile.tile_type == TileType.elevator_main_up or
            tile.tile_type == TileType.elevator_main_down)
        is_e_up    = (tile.tile_type == TileType.up_arrow or tile.tile_type == TileType.elevator_main_up)
        is_save    = tile.is_save
        is_item    = tile.is_item
        l          = Coord(-1, 0) in tile.walls
        u          = Coord(0, -1) in tile.walls
        r          = Coord(1, 0) in tile.walls
        d          = Coord(0, 1) in tile.walls
        t = (is_e_arrow, is_e_shaft, is_e_main, is_e_up, is_save, is_item, l, u, r, d)
        if tile_mapping[t] is not None:
            cmap_tuples[xy] = tile_mapping[t]
    return cmap_tuples

def split_paths(paths):
    split = []
    for path in paths:
        for itemset in path.itemsets:
            p = Path(path.start_node, path.end_node, path.coord_path, [itemset])
            split.append(p)
    return split

# Advanced map visualization with paths and items shown
# paths_with_itemsets: [([Coord], Itemset)]
# item_order: [String]
def mission_embedding(rcmap, paths, item_order, filename):
    # Want to draw each path separately
    paths = split_paths(paths)
    # [[(Coord, orientation)]]
    path_segments = [split_path(p.coord_path) for p in paths]
    #print("Paths: {}".format([path.coord_path for path in paths]))
    #print(f"Segments: {path_segments}")
    # Map segments using a dict
    track_assignments, max_track = get_segment_tracks(path_segments)
    track_size = 4
    # Add need room for 1 track, and then 2 extra tracks for walls
    # Remember that max_track is an index, so n_tracks is max_track + 1
    tile_size = track_size * (max_track + 3)
    # Create point lists
    points = get_path_points(path_segments, track_assignments, track_size, tile_size)
    #print(points)
    # Each path's color is affected by the item order
    colors = get_path_colors(paths, item_order)
    # Get the colors
    canvas = Image.new("RGB", (64 * tile_size, 32 * tile_size))
    draw_rooms(canvas, rcmap, paths, tile_size, track_size)
    #TODO: create and draw room tiles
    numpy_canvas = np.array(canvas)
    for (points, color) in zip(points, colors):
        for p1, p2 in pairwise(points):
            # Avoid length scaling for tips
            length = p1.euclidean(p2)
            tip_length = 3 / length
            cv2.arrowedLine(numpy_canvas, p1, p2, color, 2, tipLength=tip_length)
    canvas = Image.fromarray(numpy_canvas)
    canvas.save(filename)

def get_doors(rcmap, paths):
    # Coord -> {Coord directions}
    doors = defaultdict(set)
    for p in paths:
        for c1, c2 in pairwise(p.coord_path):
            map1 = rcmap[c1]
            map2 = rcmap[c2]
            d1 = c2 - c1
            d2 = c1 - c2
            if d1 in map1.walls:
                doors[c1].add(d1)
            if d2 in map2.walls:
                doors[c2].add(d2)
    return doors

def draw_rooms(canvas, rcmap, paths, tile_size, track_size):
    # Coord -> {Coord directions}
    doors = get_doors(rcmap, paths)
    room_color = (30, 30, 30)
    wall_color = (60, 60, 60)
    room_image = Image.new("RGB", (tile_size, tile_size), color=room_color)
    wall_image = Image.new("RGBA", (tile_size, tile_size), color=(0,0,0,0))
    # put wall on the right side of the image
    for x in range(track_size):
        for y in range(tile_size):
            mod_x = tile_size - x - 1
            wall_image.putpixel((mod_x, y), wall_color)
    for c, mt in rcmap.items():
        # Draw a rect of room color
        pos = c.scale(tile_size).to_tuple()
        canvas.paste(room_image, pos, 0)
        # Draw a rect of wall color in the appropriate spot
        for w in mt.walls:
            # Can do fancy math with arccos of dot product, but 
            # will give 90 degress for (0, -1)
            if w == Coord(1,0):
                angle = 0
            elif w == Coord(0, -1):
                angle = 90
            elif w == Coord(-1, 0):
                angle = 180
            elif w == Coord(0, 1):
                angle = 270
            else:
                assert False, "Bad angle!"
            wrotate = wall_image.rotate(angle)
            canvas.paste(wrotate, pos, wrotate)
        for d in doors[c]:
            # Draw a door in the appropriate spot
            pass
        pass
    pass

def get_newest_item(itemsets, order):
    assert len(itemsets) == 1
    itemset = itemsets[0]
    if len(itemset) == 0:
        return ""
    return max(itemset.__iter__(), key=lambda x: order.index(x))

def get_color(item, order):
    if item == "":
        heat = 0
    else:
        heat = (order.index(item) + 1) / len(order)
    heat_index = int(255 * heat)
    return (heat_index, 0, 255 - heat_index)

def color_legend():
    pass

def get_path_colors(paths, order):
    new_items = [get_newest_item(path.itemsets, order) for path in paths]
    return [get_color(item, order) for item in new_items]

def get_track_offset(track, track_size, tile_size):
    # 3 1 0 2 4
    offset = tile_size // 2
    direction = -1**track
    distance = (track // 2 + track % 2) * track_size
    return offset + distance * direction

def get_segment_offset(orientation, track, track_size, tile_size):
    offset = get_track_offset(track, track_size, tile_size)
    return (Coord(1,1) - orientation) * Coord(offset, offset)

def get_path_points(path_segments, tracks, track_size, tile_size):
    # For each path, the points for that path's segments
    paths_points = []
    for segments, path_tracks in zip(path_segments, tracks):
        path_points = []
        for s1, s2 in pairwise(zip(segments, path_tracks)):
            # Horizontal or vertical displacement due to first segment
            (segment1, orientation1), track1 = s1
            offset1 = get_segment_offset(orientation1, track1, track_size, tile_size)
            pos = segment1[-1]
            (segment2, orientation2), track2 = s2
            offset2 = get_segment_offset(orientation2, track2, track_size, tile_size)
            assert pos == segment2[0]
            path_points.append(pos.scale(tile_size) + offset1 + offset2)
        # Create the first and last points
        seg1_c, seg1_o = segments[0]
        center = Coord(tile_size // 2, tile_size // 2)
        first_pos = seg1_c[0].scale(tile_size)
        offset1 = get_segment_offset(seg1_o, path_tracks[0], track_size, tile_size)
        offset2 = seg1_o * center
        first_point = first_pos + offset1 + offset2
        seg2_c, seg2_o = segments[-1]
        last_pos = seg2_c[-1].scale(tile_size)
        offset1 = get_segment_offset(seg2_o, path_tracks[-1], track_size, tile_size)
        offset2 = seg2_o * center
        last_point = last_pos + offset1 + offset2
        path_points = [first_point] + path_points + [last_point]
        paths_points.append(path_points)
    return paths_points

def get_segment_tracks(path_segments):
    """ Assign non-overlapping tracks to all segments """
    # [[track_id]]
    path_assignments = []
    max_track = 0
    # Coord -> orientation -> {track_id}
    taken = defaultdict(lambda: defaultdict(set))
    for path in path_segments:
        segment_assignments = []
        for segment, orientation in path:
            all_overlaps = set()
            for c in segment:
                c_overlaps = taken[c][orientation]
                all_overlaps |= c_overlaps
            track_id = get_new_track_id(all_overlaps)
            if track_id > max_track:
                max_track = track_id
            # Assign the track id
            segment_assignments.append(track_id)
            # Update taken
            for c in segment:
                taken[c][orientation].add(track_id)
        path_assignments.append(segment_assignments)
    return path_assignments, max_track

def get_new_track_id(overlaps):
    """ Smallest int not in overlaps """
    n = 0
    while True:
        if n not in overlaps:
            return n
        n += 1

# Splits a path into horizontal and vertical segments
def split_path(path):
    segments = []
    current_segment = []
    current_direction = None
    for current_c, next_c in pairwise(path):
        new_direction = next_c - current_c
        if new_direction != current_direction:
            current_segment.append(current_c)
            if current_direction is not None:
                segments.append((current_segment, current_direction.abs()))
            current_segment = [current_c]
            current_direction = new_direction
        else:
            current_segment.append(current_c)
    current_segment.append(next_c)
    segments.append((current_segment, current_direction.abs()))
    return segments
