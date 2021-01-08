from parse_rooms import *
from constraintgraph import *
from alg_support import *

#TODO: test files in another folder?
#TODO: create a function for testing room x for a given property
if __name__ == "__main__":
    rooms = parse_rooms("encoding/rooms.txt")
    warehouse_zeelas = rooms.pop("Warehouse_Zeelas")

    fixed_items = get_fixed_items()
    #print fixed_items
    current_state = BFSItemsState("Warehouse_Zeelas_L2", set(["Item_Dummy", "Item_Dummy1"]), ItemSet(), {})

    wz_graph, wz_exits = dummy_exit_graph(warehouse_zeelas.graph, warehouse_zeelas.doors)

    finished, completed, complete_items = wz_graph.BFS_items(current_state, fixed_items=fixed_items)
    reachable_exits = {exit: finished[exit] for exit in wz_exits if len(finished[exit]) != 0}
    #print_finished(reachable_exits)
    #TODO: is current_state mutated by BFS? - so far not
    filtered_exits = filter_paths(finished, current_state, wz_exits)
    #print_finished(filtered_exits)

    ### Landing site shenanigans
    landing_site = rooms.pop("Landing_Site")
    current_state = BFSItemsState("Landing_Site_L2", set(["Item_Dummy"]), ItemSet(), {})
    ls_graph, ls_exits = dummy_exit_graph(landing_site.graph, landing_site.doors)
    finished, completed, complete_items = ls_graph.BFS_items(current_state, fixed_items=fixed_items)
    reachable_exits = {exit: finished[exit] for exit in ls_exits if len(finished[exit]) != 0}
    #print_finished(reachable_exits)
    filtered_exits = filter_paths(finished, current_state, ls_exits)
    #print_finished(filtered_exits)

    ### picking up items?
    first_missile = rooms.pop("First_Missile")
    current_state = BFSItemsState("First_Missile_R", set(), ItemSet(), {})
    fm_graph, fm_exits = dummy_exit_graph(first_missile.graph, first_missile.doors)
    finished, completed, complete_items = fm_graph.BFS_items(current_state, fixed_items=fixed_items)
    filtered_exits = filter_paths(finished, current_state, fm_exits)
    assert BFSItemsState("First_Missile_Rdummy", set(["First_Missile_M"]), ItemSet(), {}) in to_states(filtered_exits)

    ### traveling items across rooms?
    ls_graph.remove_node("Landing_Site_L2dummy")
    fm_graph.remove_node("First_Missile_Rdummy")
    exits = ls_exits + fm_exits
    exits.remove("Landing_Site_L2dummy")
    exits.remove("First_Missile_Rdummy")
    ls_graph.add_room("Landing_Site_L2", "First_Missile_R", fm_graph)
    current_state = BFSItemsState("Landing_Site_L2", set(), ItemSet(), {})
    finished, completed, complete_items = ls_graph.BFS_items(current_state, fixed_items=fixed_items)
    filtered_exits = filter_paths(finished, current_state, exits)
    assert BFSItemsState("Landing_Site_R2dummy", set(), ItemSet(["S"]), {"First_Missile_M":"S"}) in to_states(filtered_exits)

    # Boss Nodes?
    kraid = rooms.pop("Kraid")
    current_state = BFSItemsState("Kraid_L", set(), ItemSet(["CB"]), {})
    kraid_graph, kraid_exits = dummy_exit_graph(kraid.graph, kraid.doors)
    finished, _, _ = kraid_graph.BFS_items(current_state, fixed_items=fixed_items)
    print to_states(finished)
    filtered_exits = filter_paths(finished, current_state, kraid_exits)
    print_finished(filtered_exits)

    #TODO: Water Closet

    # Test dummy exit graph:
    for room in rooms.values():
        print room.name
        dummy_graph, dummy_exits = dummy_exit_graph(room.graph, room.doors)
