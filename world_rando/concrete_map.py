# Creates a concrete map based on an abstract map
# a map is a data structure:
# key1 - area (ex. "Maridia")
# key2 - (x,y) tuple
# value - MapTile
import collections

class MapTile(object):

    def __init__(self, mtype):
        self.t = mtype
        # key - (x,y) pair
        # value - list of items needed to reach
        self.d = collections.defaultdict(list)
        # list of (x,y) adjacent to this tile indicating where the walls are
        self.walls = [] #TODO: what about sloped map tiles?
        self.is_item = False

    def add_path(to_coords, with_items):
        self.d[to_coords].append(with_items)

def map_extent(cmap, region):
    """ returns the 'extent' of the cmap: two tuples of
    (minx, maxx) and (miny, maxy)"""
    mtiles = cmap[region].keys()
    if len(mtiles) == 0:
        return None
    minx = min(mtiles, key=lambda item: item[0])[0]
    miny = min(mtiles, key=lambda item: item[1])[1]
    maxx = max(mtiles, key=lambda item: item[0])[0]
    maxy = max(mtiles, key=lambda item: item[1])[1]
    return ((minx, maxx), (miny, maxy))

def map_range(cmap, region):
    """returns the actual ranges of the map, along with the placement of that range in x,y"""
    ext = map_extent(cmap, region)
    return (ext[0][1] - ext[0][0], ext[1][1] - ext[1][0]), (ext[0][0], ext[1][0])

