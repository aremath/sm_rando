# maptiles length 0x1000 bytes
# each 2 bytes is one "tile" for what that means
#

default_map_size = 0x800
default_hidden_size = 0x100

areamapLocs = {
#"area":(hiddenbitsAddrs, tilesAddrs) pc addresses
"crateria":(0x011727,0x1a9000),
"brinstar":(0x011827,0x1a8000),
"norfair":(0x011927,0x1aa000),
"wrecked_ship":(0x011a27,0x1ab000),
"maridia":(0x011b27,0x1ac000),
"tourian":(0x011c27,0x1ad000)
}

class MapTile(object):
    """ a single tile in an area map. representable as two bytes. contains logic
        to turn a set of easy to set parameters into the raw bytes"""
    def __init__(self):
        self.__default()

    def __default(self):
        self.vflip = False
        self.hflip = False
        self.color = 3
        self.tile = 0x1F
        self.hidden = True


    def __first_byte(self):
        return bytes([self.tile])

    def __second_byte(self):
        i = (0x04) * self.color
        if self.vflip:
            i += 0x80
        if self.hflip:
            i += 0x40
        return bytes([i])

    def set(self,_tuple):
        """ (vflip, hflip, tile index)"""
        if not _tuple == None:
            self.hflip = _tuple[0]
            self.vflip = _tuple[1]
            self.tile = _tuple[2]
            self.color = 3 #TODO good default stuff
            self.hidden = False

    def to_bytes(self):
        #TODO check two bytes?
        return self.__first_byte() + self.__second_byte()

    def is_not_hidden(self):
        return not self.hidden

class AreaMap(object):
    """ a set of map tiles is an area map, can generate the whole map data
        including the midden bitmap"""
    def __init__(self):
        self.tile_list = [MapTile()] * default_map_size

    def __right_size(self):
        if (len(self.tile_list) == default_map_size):
            return True
        else:
            return False

    def __is_right_size(self):
        if not self.__right_size():
            assert False, "Wrong map size"

    def map_to_bytes(self):
        self.__is_right_size()
        x = bytes()
        for tile in self.tile_list:
            x += tile.to_bytes()
        return x

    def hidden_to_bytes(self):
        l = []
        t = 0
        self.__is_right_size()
        for i in range(len(self.tile_list)):
            if i > 0 and ((i % 8) == 0):
                l.append(t)
                t = 0
            t *= 2
            t += self.tile_list[i].hidden
        l.append(t)
        assert len(bytes(l)) == default_hidden_size
        return bytes(l)

#TODO: hidden problems
def tuples_to_amap(cmap_tuples):
    """takes a dict with key - xy, value - (hflip, vflip, index) and creates the appropriate amap"""
    amap = AreaMap()
    # The map is represented on the ROM as two 32x32 arrays instead of one 64x64 array.
    for submap in range(2):
        for x in range(32):
            for y in range(32):
                cmap_x = x + (submap * 32)
                cmap_y = y - 1 #offset
                cmap_vs = (cmap_x, cmap_y)
                #print(cmap_vs, submap)
                if cmap_vs in cmap_tuples:
                    index = x + (y*32) + (submap * 0x400) #TODO: index out of range problems?
                    new_tile = MapTile()
                    new_tile.set(cmap_tuples[cmap_vs])
                    amap.tile_list[index] = new_tile
    return amap
