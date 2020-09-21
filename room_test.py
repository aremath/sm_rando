from world_rando import generate

if __name__ == "__main__":
    abstract_map_info = generate.generate_abstract_map()
    concrete_map_info = generate.generate_concrete_map(abstract_map_info)
    room_info = generate.generate_rooms(concrete_map_info)
    generate.print_stats(concrete_map_info[-1])

    generate.visualize_concrete_maps(concrete_map_info)
    generate.visualize_rooms(room_info)

