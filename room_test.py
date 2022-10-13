import random
from world_rando import generate
from world_rando.settings import default_settings as s

if __name__ == "__main__":
    random.seed(0)
    abstract_map_info = generate.generate_abstract_map(s)
    concrete_map_info = generate.generate_concrete_map(s, abstract_map_info)
    generate.visualize_concrete_maps(concrete_map_info)
    generate.print_stats(concrete_map_info[-1])
    room_info = generate.generate_rooms(s, concrete_map_info)
    generate.visualize_rooms(room_info)

