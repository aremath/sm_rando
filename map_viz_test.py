from world_rando import concrete_map
from world_rando import map_viz

if __name__ == "__main__":
    example_map = {}
    example_map["Maridia"] = {}

    example_map["Maridia"][(2,2)] = concrete_map.MapTile("")
    example_map["Maridia"][(2,2)].walls = [(1,2), (2,1), (3,2), (2,3)]

    example_map["Maridia"][(10,10)] = concrete_map.MapTile("")
    example_map["Maridia"][(10,10)].is_item = True
    example_map["Maridia"][(10,10)].walls = [(10,11), (11,10)]

    example_map["Maridia"][(10,9)] = concrete_map.MapTile("")
    example_map["Maridia"][(10,9)].walls = [(10,8), (11,9)]

    example_map["Maridia"][(9,10)] = concrete_map.MapTile("")
    example_map["Maridia"][(9,10)].walls = [(9,11), (8,10)]

    example_map["Maridia"][(9,9)] = concrete_map.MapTile("")
    example_map["Maridia"][(9,9)].walls = [(9,8), (8,9)]

    example_map["Maridia"][(5,5)] = concrete_map.MapTile("")
    example_map["Maridia"][(5,5)].walls = [(5,6),(5,4)]

    example_map["Maridia"][(4,5)] = concrete_map.MapTile("")
    example_map["Maridia"][(4,5)].walls = [(4,6),(4,4),(3,4)]

    map_viz.map_viz(example_map, "Maridia", "map.png")
