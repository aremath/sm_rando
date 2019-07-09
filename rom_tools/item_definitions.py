# Author - Aremath
# contains the bytes for writing to files.
# so does item_definitions.txt, but parsing it is a pain :(
# thanks to dessyreqt for the item memory values!
import collections

def make_item_definitions():
	# key1 = item_type (M, SJ, SA, etc)
	# key1 = location_type ((N)ormal, (C)hozo, or (H)idden)
	# value = bytes to write to get that item.
	item_definitions = collections.defaultdict(dict)

	# Missiles
	item_definitions["M"]["N"] = b"\xdb\xee"
	item_definitions["M"]["C"] = b"\x2f\xef"
	item_definitions["M"]["H"] = b"\x83\xef"

	# Super Missiles
	item_definitions["S"]["N"] = b"\xdf\xee"
	item_definitions["S"]["C"] = b"\x33\xef"
	item_definitions["S"]["H"] = b"\x87\xef"

	# Charge Beam
	item_definitions["CB"]["N"] = b"\xeb\xee"
	item_definitions["CB"]["C"] = b"\x3f\xef"
	item_definitions["CB"]["H"] = b"\x93\xef"

	# Wave Beam
	item_definitions["WB"]["N"] = b"\xfb\xee"
	item_definitions["WB"]["C"] = b"\x4f\xef"
	item_definitions["WB"]["H"] = b"\xa3\xef"

	# Ice Beam
	item_definitions["IB"]["N"] = b"\xef\xee"
	item_definitions["IB"]["C"] = b"\x43\xef"
	item_definitions["IB"]["H"] = b"\x97\xef"

	# Plasma Beam
	item_definitions["PLB"]["N"] = b"\x13\xef"
	item_definitions["PLB"]["C"] = b"\x67\xef"
	item_definitions["PLB"]["H"] = b"\xbb\xef"

	# Spazer
	item_definitions["Spazer"]["N"] = b"\xff\xee"
	item_definitions["Spazer"]["C"] = b"\x53\xef"
	item_definitions["Spazer"]["H"] = b"\xa7\xef"

	# X-Ray
	item_definitions["XR"]["N"] = b"\x0f\xef"
	item_definitions["XR"]["C"] = b"\x63\xef"
	item_definitions["XR"]["H"] = b"\xb7\xef"

	# Grapple Beam
	item_definitions["G"]["N"] = b"\x17\xef"
	item_definitions["G"]["C"] = b"\x6b\xef"
	item_definitions["G"]["H"] = b"\xbf\xef"

	# Energy Tank
	item_definitions["E"]["N"] = b"\xd7\xee"
	item_definitions["E"]["C"] = b"\x2b\xef"
	item_definitions["E"]["H"] = b"\x7f\xef"

	# Bombs
	item_definitions["B"]["N"] = b"\xe7\xee"
	item_definitions["B"]["C"] = b"\x3b\xef"
	item_definitions["B"]["H"] = b"\x8f\xef"

	# Power Bombs
	item_definitions["PB"]["N"] = b"\xe3\xee"
	item_definitions["PB"]["C"] = b"\x37\xef"
	item_definitions["PB"]["H"] = b"\x8b\xef"

	# Hi Jump
	item_definitions["HJ"]["N"] = b"\xf3\xee"
	item_definitions["HJ"]["C"] = b"\x47\xef"
	item_definitions["HJ"]["H"] = b"\x9b\xef"

	# Space Jump
	item_definitions["SJ"]["N"] = b"\x1b\xef"
	item_definitions["SJ"]["C"] = b"\x6f\xef"
	item_definitions["SJ"]["H"] = b"\xc3\xef"

	# Speed Booster
	item_definitions["SB"]["N"] = b"\xf7\xee"
	item_definitions["SB"]["C"] = b"\x4b\xef"
	item_definitions["SB"]["H"] = b"\x9f\xef"

	# Spring Ball - Best item in the game
	item_definitions["SPB"]["N"] = b"\x03\xef"
	item_definitions["SPB"]["C"] = b"\x57\xef"
	item_definitions["SPB"]["H"] = b"\xab\xef"

	# Varia Suit
	item_definitions["V"]["N"] = b"\x07\xef"
	item_definitions["V"]["C"] = b"\x5b\xef"
	item_definitions["V"]["H"] = b"\xaf\xef"

	# Gravity Suit
	item_definitions["GS"]["N"] = b"\x0b\xef"
	item_definitions["GS"]["C"] = b"\x5f\xef"
	item_definitions["GS"]["H"] = b"\xb3\xef"

	# Morph Ball
	item_definitions["MB"]["N"] = b"\x23\xef"
	item_definitions["MB"]["C"] = b"\x77\xef"
	item_definitions["MB"]["H"] = b"\xcb\xef"

	# Reserve Tank
	item_definitions["RT"]["N"] = b"\x27\xef"
	item_definitions["RT"]["C"] = b"\x7b\xef"
	item_definitions["RT"]["H"] = b"\xcf\xef"

	# Screw Attack
	item_definitions["SA"]["N"] = b"\x1f\xef"
	item_definitions["SA"]["C"] = b"\x73\xef"
	item_definitions["SA"]["H"] = b"\xc7\xef"

	return item_definitions

