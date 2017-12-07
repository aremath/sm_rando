from parse_rooms import *
from graph import *
import alg_support

#TODO: test files in another folder?
#TODO: clean up the dumb Room object! >:(

if __name__ == "__main__":
    rooms = parse_rooms("encoding/testcases/warehouse_zeelas.txt")
    warehouse_zeelas = rooms.pop("Warehouse_Zeelas")

    fixed_items = alg_support.get_fixed_items()
    #print fixed_items
    current_state = BFSItemsState("Warehouse_Zeelas_L1", set(["Item_Dummy", "Item_Dummy1"]), ItemSet(), {})

    wz_graph, wz_exits = alg_support.dummy_exit_graph(warehouse_zeelas[0].graph, warehouse_zeelas[1])
    print wz_exits
    print wz_graph

    finished, completed, complete_items = wz_graph.BFS_items(current_state, fixed_items=fixed_items)
    reachable_exits = {exit: finished[exit] for exit in wz_exits if len(finished[exit]) != 0}
    print reachable_exits
    #TODO: is current_state mutated by BFS?
    filtered_exits = alg_support.filter_paths(finished, current_state, wz_exits)
    print filtered_exits
    #TODO: UH OH
