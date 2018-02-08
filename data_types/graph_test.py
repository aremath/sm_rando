from parse_rooms import *
from graph import *

if __name__ == "__main__":
	rooms = parse_rooms("encoding/rooms.txt")
	#finished, completed, complete_items = rooms["Ice_Beam"][0].graph.BFS_items("Ice_Beam_L")

	finished, completed, complete_items = rooms["Frog_Speedway"].graph.BFS_items("Frog_Speedway_R", wildcards=set(["Item_Dummy"]))
	print "finished"
	print finished
