from concrete_map import *
import map_viz
import random

def rand_d(x,y):
    return euclidean(x,y) + random.uniform(0,9)

if __name__ == "__main__":
    start = MCoords(4,4)
    end = MCoords(4,34)
    offers, finished = map_search(start, end, dist=lambda x,y: rand_d(x,y))
    path = get_path(offers, start, end)
    bfs_map = {}
    bfs_map["E"] = {}
    for xy in path:
        bfs_map["E"][xy] = MapTile("")
    elide_walls(bfs_map, "E")
    map_viz.map_viz(bfs_map, "E", "map.png", "../encoding/map_tiles")

