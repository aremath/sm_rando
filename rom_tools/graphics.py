from . import rom_manager
from .address import *
from .compress import decompress

import numpy as np
from PIL import Image
from PIL import ImageOps

# Important Pointers
cre_tile_addr = Address(0xb98000, mode="snes")
cre_tile_table_addr = Address(0xb9a09d, mode="snes")
tileset_table_addr = Address(0x8fe6a2, mode="snes")

# Read the table of tilesets
def get_tileset_table(rom):
    tilesets = rom.read_list(tileset_table_addr, 9, 0x1d, compressed=False)
    # Split them into 3 3-byte pointers
    tilesets = [[t[0:3], t[3:6], t[6:9]] for t in tilesets]
    # Make those into Addresses
    tilesets_addrs = []
    for t in tilesets:
        l = list(map(lambda x: Address(int.from_bytes(x, byteorder='little'), mode='snes'), t))
        tilesets_addrs.append(l)
    return tilesets_addrs

def get_tileset(rom, tileset_index, tileset_table):
    tile_table_addr, tilesheet_addr, palette_addr = tileset_table[tileset_index]
    palette = palette_image(rom, palette_addr)
    tile_table = get_tile_table(rom, tile_table_addr)
    tile_sheet = get_tilesheet(rom, tilesheet_addr)
    return (tile_table, tile_sheet, palette)

## Palette
# 15 bit BGR, highest bit unused
def get_rgb(color):
    r_mask = 0b11111
    g_mask = r_mask << 5
    b_mask = r_mask << 10
    # Mask out the correct 5-bit values
    r5 = color & r_mask
    g5 = (color & g_mask) >> 5
    b5 = (color & b_mask) >> 10
    # Upscale them to 8-bit
    r8 = r5 << 3
    g8 = g5 << 3
    b8 = b5 << 3
    return (r8, g8, b8)

def palette_image(rom, palette_addr):
    # 16 x 8 palette with 2 bytes per pixel
    palette_bytes = rom.read_list(palette_addr, 2, 128)
    palette_colors = list(map(lambda x: get_rgb(int.from_bytes(x, byteorder='little')), palette_bytes))
    palette = Image.new("RGBA", (16,8), "black")
    for x in range(16):
        for y in range(8):
            index = y * 16 + x
            r,g,b = palette_colors[index]
            if x == 0:
                a = 0
            # Index 0 is transparent
            else:
                a = 255
            palette.putpixel((x,y), (r,g,b,a))
    return palette

## Subtile Sheet
def get_tilesheet(rom, address):
    return rom.read_list(address, 32, 640, check_length=False)

def get_cre_tilesheet(rom):
    return rom.read_list(cre_tile_addr, 32, 384)

def get_pixel_color_index(tile, x, y, bpp=4):
    palette_index = 0
    for i in range(bpp // 2):
        for j in range(2):
            palette_index |= (tile[y * 2 + i * 0x10 + j] >> 7 - x & 1) << i * 2 + j
    return palette_index
	
def build_subtile(subtile_bytes, palette, palette_index_y):
    subtile = Image.new("RGBA", (8,8), "black")
    for x in range(8):
        for y in range(8):
            palette_index_x = get_pixel_color_index(subtile_bytes, x, y)
            palette_color = palette.getpixel((palette_index_x, palette_index_y))
            subtile.putpixel((x, y), palette_color)
    return subtile

# Arrange a list of images into one big image
def tiled_image(images, width, height):
    assert width * height == len(images)
    i = images[0]
    i_width = i.width
    i_height = i.height
    out = Image.new("RGBA", (width * i_width, height * i_height), "black")
    for index, image in enumerate(images):
        x = index % width
        y = index // width
        out.paste(image, (x * i_width, y * i_height))
    return out

def save_subtile_image(filename, subtiles, width, height, palette, palette_y=0):
    subtile_images = [build_subtile(x, palette, palette_y) for x in subtiles]
    subtile_image = tiled_image(subtile_images, width, height)
    subtile_image.save(filename)
	
## Tile Table
def get_tile_table(rom, address):
    return rom.read_list(address, 8, 768)

def get_cre_tile_table(rom):
    return rom.read_list(cre_tile_table_addr, 8, 256)

# PJBoy said that the tilesheet is up to 0x280 tilesheet-specific tiles followed by 0x180 CRE tiles for a total of
# 0x400 = 1024 tiles
# SCE uses 0x280 tiles before starting to overwrite the CRE, but isn't required to use all of them
def get_tile_bytes(index, sce_tilesheet, cre_tilesheet):
    # Index is 10 bytes
    assert index >= 0 and index < 0x400, hex(index)
    # SCE takes priority over CRE since it is copied on top of the CRE if it is larger than the normal 0x280 bytes
    if index < len(sce_tilesheet):
        return sce_tilesheet[index]
    # Otherwise it can index into the CRE which is always at 0x280 and above
    elif index >= 0x280:
        return cre_tilesheet[index - 0x280]
    # Something is going wrong if it is indexing a value between the end of the SCE and before the
    # beginning of the CRE
    else:
        assert False, hex(index)
        
def apply_flips(image, flips):
    # y
    if flips[0]:
        image = ImageOps.flip(image)
    # x
    if flips[1]:
        image = ImageOps.mirror(image)
    return image

# Two bytes
# YXLP PPTT TTTT TTTT    
def get_subtile_def(subtile_bytes):
    q = int.from_bytes(subtile_bytes, byteorder='little')
    y_flip = (q >> 15) & 0b1
    x_flip = (q >> 14) & 0b1
    layer_priority = (q >> 13) & 0b1
    palette_index_y = (q >> 10) & 0b111
    tile_index = q & 0b0000001111111111
    return (y_flip, x_flip, layer_priority, palette_index_y, tile_index)

def get_subtile_image(subtile_def, sce_tilesheet, cre_tilesheet, palette):
    y_flip, x_flip, layer_priority, palette_index_y, tile_index = subtile_def
    tile_bytes = get_tile_bytes(tile_index, sce_tilesheet, cre_tilesheet)
    subtile_image = build_subtile(tile_bytes, palette, palette_index_y)
    subtile_image = apply_flips(subtile_image, (y_flip, x_flip))
    return subtile_image
    
def get_tile_image(tile_bytes, sce_tilesheet, cre_tilesheet, palette):
    assert len(tile_bytes) == 8
    subtile_defs = [tile_bytes[i:i+2] for i in range(0,8,2)]
    subtile_images = list(map(lambda x: get_subtile_image(get_subtile_def(x),
                                                    sce_tilesheet, cre_tilesheet, palette), subtile_defs))
    tile_image = tiled_image(subtile_images, 2, 2)
    return tile_image

def tile_images(tile_table, sce_subtiles, cre_subtiles, palette):
    return [get_tile_image(i, sce_subtiles, cre_subtiles, palette) for i in tile_table]

def save_tile_table_image(filename, tile_table, width, height, sce_subtiles, cre_subtiles, palette):
    t_images = tile_images(tile_table, sce_subtiles, cre_subtiles, palette)
    out = tiled_image(t_images, width, height)
    out.save(filename)

## Level Data

def get_tile(index, sce_tile_table, cre_tile_table):
    # Index is 10 bytes
    assert index >= 0 and index < 0x400, hex(index)
    # Index into the CRE
    if index < 0x100:
        return cre_tile_table[index]
    else:
        return sce_tile_table[index - 0x100]
    
def level_image(level, sce_tile_table_images, cre_tile_table_images):
    l_image = Image.new("RGBA", (level.dimensions.x * 16, level.dimensions.y * 16), "black")
    for c in level.itercoords():
        tile = level[c]
        tile_image = get_tile(tile.texture.index, sce_tile_table_images, cre_tile_table_images)
        tile_image = apply_flips(tile_image, tile.texture.flips)
        # Third argument is the alpha mask
        l_image.paste(tile_image, (c.x * 16, c.y * 16), tile_image)
    return l_image

def level_arrays_image(layer1, sce_tile_table_images, cre_tile_table_images):
    l_image = Image.new("RGBA", tuple((layer1.shape * np.array([16, 16]))), "black")
    it = np.nditer(layer1, flags=["multi_index", "refs_ok"])
    for tile_ref in it:
        # What the hell, numpy
        tile = tile_ref.item()
        tile_image = get_tile(tile.texture.texture_index, sce_tile_table_images, cre_tile_table_images)
        flips = (tile.texture.hflip, tile.texture.vflip)
        tile_image = apply_flips(tile_image, flips)
        # Third argument is the alpha mask
        l_image.paste(tile_image, tuple(it.multi_index * np.array([16, 16])), tile_image)
    return l_image

#TODO: decide on 'subtiles' vs. 'tilesheet'
def level_from_tileset(rom, level, tileset_index):
    # Set up by getting the tile images for the SCE and CRE by parsing the tile table
    tileset_table = get_tileset_table(rom)
    sce_tile_table, sce_tile_sheet, sce_palette = get_tileset(rom, tileset_index, tileset_table)
    cre_tile_sheet = get_cre_tilesheet(rom)
    cre_tile_table = get_cre_tile_table(rom)
    cre_tt_image = tile_images(cre_tile_table, sce_tile_sheet, cre_tile_sheet, sce_palette)
    sce_tt_image = tile_images(sce_tile_table, sce_tile_sheet, cre_tile_sheet, sce_palette)
    return level_image(level, sce_tt_image, cre_tt_image)

def layer1_image_from_tileset(rom, layer1, tileset_index):
    # Set up by getting the tile images for the SCE and CRE by parsing the tile table
    tileset_table = get_tileset_table(rom)
    sce_tile_table, sce_tile_sheet, sce_palette = get_tileset(rom, tileset_index, tileset_table)
    cre_tile_sheet = get_cre_tilesheet(rom)
    cre_tile_table = get_cre_tile_table(rom)
    cre_tt_image = tile_images(cre_tile_table, sce_tile_sheet, cre_tile_sheet, sce_palette)
    sce_tt_image = tile_images(sce_tile_table, sce_tile_sheet, cre_tile_sheet, sce_palette)
    return level_arrays_image(layer1, sce_tt_image, cre_tt_image)

