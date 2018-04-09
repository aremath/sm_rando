
class Room(object):

    def __init__(self, tiles, graph=None):
        self.tiles = tiles
        self.enemies = []
        self.plms = []
        self.graph = graph

    def translate(self):
        #produce a Jake room from this
        pass

#TODO: Door needs to contain some info about what ROOMS it connects, not just what tiles...
# or maybe the tiles on the cmap know what room they are in.
class Door(object):

    def __init__(self, tile1, tile2):
        #TODO: assert that tile1 is next to tile2
        self.tiles = (tile1, tile2)

    def __hash__(self):
        #TODO: is this real?
        return hash(self.tiles)

class Tile(object):

    def __init__(self, vtile=None, vflip=None, ptile=None, pflip=None):
        """ vtile is an index into the virtual tile table
            vflip is a (bool, bool) indicating horizontal and vertical flip
            ptile and pflip are the same but for the physical tile table"""
        self.vtile = vtile
        self.vflip = vflip
        self.ptile = ptile
        self.pflip = pflip

    #TODO
    def to_bytes(self):
        pass
