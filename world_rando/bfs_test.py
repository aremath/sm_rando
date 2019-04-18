from concrete_map import *
import map_viz
import random

if __name__ == "__main__":
    nnodes = 0
    start = MCoords(15,0)
    end = MCoords(15,30)
    offers, finished = map_search(start, end, dist=rand_d)
    path = get_path(offers, start, end)
    nnodes += len(path)
    bfs_map = {}
    bfs_map["E"] = {}
    # put the tiles into the map
    for xy in path:
        bfs_map["E"][xy] = MapTile("")

    start = MCoords(0, 15)
    end = MCoords(30, 15)
    offers, finished = map_search(start, end, dist=rand_d)
    path = get_path(offers, start, end)
    nnodes += len(path)
    for xy in path:
        bfs_map["E"][xy] = MapTile("")

    # partition it into rooms
    _, _ = random_rooms(int(nnodes/3), bfs_map, "E")
    #elide_walls(bfs_map, "E")
    map_viz.map_viz(bfs_map, "E", "map.png", "../encoding/map_tiles")

