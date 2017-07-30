# Author - Ross Mawhorter
# test function to ensure parser is working properly.

import parser

if __name__ == "__main__":

	rooms = parser.parse_rooms("encoding/rooms.txt")

	print rooms["Frog_Speedway"]

	# TODO: actually test something too :P do stuff