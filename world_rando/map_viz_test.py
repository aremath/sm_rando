from concrete_map import *
import map_viz

if __name__ == "__main__":
    example_map = {}
    example_map["Maridia"] = {}

    example_map["Maridia"][MCoords(2,2)] = MapTile("")
    example_map["Maridia"][MCoords(2,2)].walls = [MCoords(1,2), MCoords(2,1), MCoords(3,2), MCoords(2,3)]

    example_map["Maridia"][MCoords(10,10)] = MapTile("")
    example_map["Maridia"][MCoords(10,10)].is_item = True
    example_map["Maridia"][MCoords(10,10)].walls = [MCoords(10,11), MCoords(11,10)]

    example_map["Maridia"][MCoords(10,9)] = MapTile("")
    example_map["Maridia"][MCoords(10,9)].walls = [MCoords(10,8), MCoords(11,9)]

    example_map["Maridia"][MCoords(9,10)] = MapTile("")
    example_map["Maridia"][MCoords(9,10)].walls = [MCoords(9,11), MCoords(8,10)]

    example_map["Maridia"][MCoords(9,9)] = MapTile("")
    example_map["Maridia"][MCoords(9,9)].walls = [MCoords(9,8), MCoords(8,9)]

    example_map["Maridia"][MCoords(5,5)] = MapTile("")
    example_map["Maridia"][MCoords(5,5)].walls = [MCoords(5,6), MCoords(5,4)]

    example_map["Maridia"][MCoords(4,5)] = MapTile("")
    example_map["Maridia"][MCoords(4,5)].walls = [MCoords(4,6),MCoords(4,4),MCoords(3,4)]

    map_viz.map_viz(example_map, "Maridia", "map.png", "../encoding/map_tiles")
