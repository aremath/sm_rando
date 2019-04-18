import graphviz
from functools import reduce

boss_rooms = ["Kraid", "Ridley", "Draygon", "Phantoon"]
miniboss_rooms = ["Spore Spawn", "Botwoon", "Crocomire", "Bomb Torizo", "Golden Torizo"]

def make_spoiler_graph(door_connections, spoiler_filename):
    # make a set of all the rooms
    rooms = set()
    for ldoor, rdoor in door_connections:
        rooms.add(get_room_name(ldoor))
        rooms.add(get_room_name(rdoor))
    dot = graphviz.Graph()
    for room_name in rooms:
        if room_name == "Landing Site":
            dot.node(room_name, room_name, color='blue', style='filled')
        elif room_name in boss_rooms:
            dot.node(room_name, room_name, color='red', style='filled')
        elif room_name in miniboss_rooms:
            dot.node(room_name, room_name, color='green', style='filled')
        elif room_name == "Statues":
            dot.node(room_name, room_name, color='yellow', style='filled')
        elif room_name == "Escape 4":
            dot.node(room_name, room_name, color='purple', style='filled')
        else:
            dot.node(room_name, room_name)
    for ldoor, rdoor in door_connections:
        dot.edge(get_room_name(ldoor), get_room_name(rdoor), label=(ldoor.split("_")[-1] + " to " + rdoor.split("_")[-1]))
    dot.render(spoiler_filename + ".graph")

# gets the name of the room for a given door
def get_room_name(door):
    return reduce(lambda x, y: x + " " + y, door.split("_")[:-1])

