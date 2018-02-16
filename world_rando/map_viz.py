# visualizes a concrete map of the form laid out in concrete_map.py

from concrete_map import *
from PIL import Image

#TODO: use path to find the files?
def load_map_tiles(map_dir):
    i0w  = Image.open(map_dir + "/0wall.png")
    i1w  = Image.open(map_dir + "/1wall.png")
    i2w  = Image.open(map_dir + "/2wall.png")
    i2wp = Image.open(map_dir + "/2wallpipe.png")
    i3w  = Image.open(map_dir + "/3wall.png")
    i4w  = Image.open(map_dir + "/4wall.png")
    ba  = Image.open(map_dir + "/blank_alpha.png")
    ia  = Image.open(map_dir + "/item_alpha.png")
    wall_dict = {"0w" : i0w,
                 "1w" : i1w,
                 "2w" : i2w,
                 "2wp": i2wp,
                 "3w" : i3w,
                 "4w" : i4w}
    return wall_dict, ba, ia

def is_below(xy1, xy2):
    """is xy2 directly below xy1?"""
    return xy2 == xy1.down()

def is_left(xy1, xy2):
    return xy2 == xy1.left()

def is_right(xy1, xy2):
    return xy2 == xy1.right()

def is_above(xy1, xy2):
    return xy2 == xy1.up()

def has(wall_list, f, xy):
    """does wall_list have a wall satisfying property f?"""
    return len([w for w in wall_list if f(xy, w)]) > 0

def find_image(walls, xy):
    """returns which image to use, and how to rotate it"""
    nwalls = len(walls)
    # unoptimized spaghetti code
    if nwalls == 0:
        return "0w", 0
    elif nwalls == 1:
        if has(walls, is_left, xy): 
            return "1w", 0
        if has(walls, is_above, xy):
            return "1w", 270
        if has(walls, is_right, xy):
            return "1w", 180
        if has(walls, is_below, xy):
            return "1w", 90
    elif nwalls == 2:
        if has(walls, is_below, xy) and has(walls, is_above, xy):
            return "2wp", 90
        if has(walls, is_left, xy) and has(walls, is_right, xy):
            return "2wp", 0
        if has(walls, is_left, xy) and has(walls, is_above, xy):
            return "2w", 0
        if has(walls, is_above, xy) and has(walls, is_right, xy):
            return "2w", 270
        if has(walls, is_right, xy) and has(walls, is_below, xy):
            return "2w", 180
        if has(walls, is_below, xy) and has(walls, is_left, xy):
            return "2w", 90
    elif nwalls == 3:
        if not has(walls, is_right, xy):
            return "3w", 0
        if not has(walls, is_below, xy):
            return "3w", 270
        if not has(walls, is_left, xy):
            return "3w", 180
        if not has(walls, is_above, xy):
            return "3w", 90
    elif nwalls == 4:
        return "4w", 0
       
def map_viz(cmap, region, filename, map_dir):
    mrange, mins = map_range(cmap, region)
    map_image = Image.new("RGBA", ((mrange.x+1)*16, (mrange.y+1)*16), "black")
    # bind the current region for easy re-use
    bregion = cmap[region]
    wmap, blank, item = load_map_tiles(map_dir)
    for x in range(mrange.x+1):
        for y in range(mrange.y+1):
            relxy = MCoords(x, y) + mins
            xy = (x,y)
            if relxy in bregion:
                mtile = bregion[relxy]
                image_name, rotation = find_image(mtile.walls, relxy)
                image = wmap[image_name]
                imrotate = image.rotate(rotation)
                map_image.paste(imrotate, (x*16,y*16), imrotate)
                if mtile.is_item:
                    map_image.paste(item, (x*16,y*16), item)
            else:
                # it's a blank
                map_image.paste(blank, (x*16,y*16), blank)
    map_image.save(filename)
    return map_image
