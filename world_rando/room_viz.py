# visualizes a concrete map of the form laid out in concrete_map.py
import collections #defaultdict
from .coord import *
#from .room_dtypes import *
from PIL import Image
from PIL import ImageOps

# Cuts an image into xsize x ysize images as a list
def image_grid(image, xsize, ysize):
    # Check that the sizes are compatible
    assert image.size[0] % xsize == 0, image.size[0]
    assert image.size[1] % ysize == 0, image.size[1]
    ims = []
    for y in range(0, image.size[1], ysize):
        for x in range(0, image.size[0], xsize):
            crop = image.crop((x, y, x + xsize, y + ysize))
            ims.append(crop)
    return ims

def load_room_tiles(room_dir):
    # Tile Types
    bomb = Image.open(room_dir + "/bomb.png")
    crumble = Image.open(room_dir + "/crumble.png")
    crumble_grapple = Image.open(room_dir + "/crumble.png")
    door = Image.open(room_dir + "/door.png")
    error = Image.open(room_dir + "/error.png")
    grapple = Image.open(room_dir + "/grapple.png")
    h_copy = Image.open(room_dir + "/h_copy.png")
    left_conveyor = Image.open(room_dir + "/left_conveyor.png")
    power_bomb = Image.open(room_dir + "/power_bomb.png")
    quicksand = Image.open(room_dir + "/quicksand.png")
    right_conveyor = Image.open(room_dir + "/right_conveyor.png")
    sandfall = Image.open(room_dir + "/sandfall.png")
    shot_block = Image.open(room_dir + "/shot_block.png")
    solid = Image.open(room_dir + "/solid.png")
    speedbooster = Image.open(room_dir + "/speedbooster.png")
    spike = Image.open(room_dir + "/spike.png")
    super_block = Image.open(room_dir + "/super.png")
    v_copy = Image.open(room_dir + "/v_copy.png")
    slopes = image_grid(Image.open(room_dir + "/slopes.png"), 16, 16)
    images = {
        "bomb" : bomb,
        "crumble" : crumble,
        "crumble_grapple" : crumble_grapple,
        "door" : door,
        "error" : error,
        "grapple" : grapple,
        "h_copy" : h_copy,
        "left_conveyor" : left_conveyor,
        "power_bomb" : power_bomb,
        "quicksand" : quicksand,
        "right_conveyor" : right_conveyor,
        "sandfall" : sandfall,
        "shot_block" : shot_block,
        "solid" : solid,
        "speedbooster" : speedbooster,
        "spike" : spike,
        "super_block" : super_block,
        "v_copy" : v_copy
    }
    return images, slopes

def find_image(tile, images, slopes):
    """returns which image to use"""
    tindex = tile.tile_type.index
    bts = tile.tile_type.bts
    # more unoptimized spaghetti code
    # Air
    if tindex == 0x0 and bts == 0:
        return None
    # Slopes
    elif tindex == 0x1:
        hflip, vflip, index = tile.get_slope_info()
        img = slopes[index]
        if hflip:
            img = ImageOps.mirror(img)
        if vflip:
            img = ImageOps.flip(img)
        return img
    # Right conveyor
    elif tindex == 0x3 and bts == 0x8:
        return images["right_conveyor"]
    # Left conveyor
    elif tindex == 0x3 and bts == 0x9:
        return images["left_conveyor"]
    # Quicksand
    elif tindex == 0x3 and bts == 0x82:
        return images["quicksand"]
    # Sandfall
    elif tindex == 0x3 and bts == 0x85:
        return images["sandfall"]
    # H-Copy
    elif tindex == 0x5:
        return images["h_copy"]
    # Solid
    elif tindex == 0x8 and bts == 0x0:
        return images["solid"]
    # Door
    elif tindex == 0x9:
        return images["door"]
    # Spike
    elif tindex == 0xA:
        return images["spike"]
    # Crumble
    elif tindex == 0xB:
        return images["crumble"]
    # Speed Booster #TODO
    elif tindex == 0xB and bts == 0xE:
        return images["speedbooster"]
    # Power Bomb
    elif tindex == 0xC and (bts == 0x8 or bts == 0x9):
        return images["power_bomb"]
    # Super Missile
    elif tindex == 0xC and (bts == 0xA or bts == 0xB):
        return images["super_missile"]
    # Shot
    elif tindex == 0xC:
        return images["shot_block"]
    # V-Copy
    elif tindex == 0xD:
        return images["v_copy"]
    # Grapple
    elif tindex == 0xE and bts == 0x0:
        return images["grapple"]
    elif tindex == 0xE and (bts == 0x1 or bts == 0x2):
        return images["crumble_grapple"]
    # Bomb
    elif tindex == 0xF:
        return images["bomb"]
    else:
        return images["error"]
       
def room_viz(level, filename, room_dir):
    room_image = Image.new("RGBA", ((level.dimensions.x)*16, (level.dimensions.y)*16), "white")
    images, slopes = load_room_tiles(room_dir)
    for c in level.itercoords():
        rtile = level[c]
        img = find_image(rtile, images, slopes)
        if img is not None:
            room_image.paste(img, (c.x*16,c.y*16), img)
    room_image.save(filename)
    return room_image


