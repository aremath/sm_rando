from parse_rooms import *
from graph import *
import alg_support

#TODO: test files in another folder?
#TODO: clean up the dumb Room object! >:(

if __name__ == "__main__":
	rooms = parse_rooms("encoding/testcases/warehouse_zeelas.txt")
        current_node = "Warehouse_Zeelas_L1"
        warehouse_zeelas = rooms.pop("Warehouse_Zeelas")

        wz_graph, wz_exits = alg_support.dummy_exit_graph(warehouse_zeelas[0].graph, warehouse_zeelas[1])
        print wz_exits
        print wz_graph

	finished, completed, complete_items = wz_graph.BFS_items(current_node, wildcards=set(["Item_Dummy", "Item_Dummy1"]))
        reachable_exits = {exit: finished[exit] for exit in wz_exits if len(finished[exit]) != 0}
	print reachable_exits
        #TODO: UH OH
