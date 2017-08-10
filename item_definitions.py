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
	item_definitions["M"]["N"] = "\xdb\xee"
	item_definitions["M"]["C"] = "\x2f\xef"
	item_definitions["M"]["H"] = "\x83\xef"

	# Super Missiles
	item_definitions["S"]["N"] = "\xdf\xee"
	item_definitions["S"]["C"] = "\x33\xef"
	item_definitions["S"]["H"] = "\x87\xef"

	# Charge Beam
	item_definitions["CB"]["N"] = "\xeb\xee"
	item_definitions["CB"]["C"] = "\x3f\xef"
	item_definitions["CB"]["H"] = "\x93\xef"

	# Wave Beam
	item_definitions["WB"]["N"] = "\xfb\xee"
	item_definitions["WB"]["C"] = "\x4f\xef"
	item_definitions["WB"]["H"] = "\xa3\xef"

	# Ice Beam
	item_definitions["IB"]["N"] = "\xef\xee"
	item_definitions["IB"]["C"] = "\x43\xef"
	item_definitions["IB"]["H"] = "\x97\xef"

	# Plasma Beam
	item_definitions["PLB"]["N"] = "\x13\xef"
	item_definitions["PLB"]["C"] = "\x67\xef"
	item_definitions["PLB"]["H"] = "\xbb\xef"

	# Spazer
	item_definitions["Spazer"]["N"] = "\xff\xee"
	item_definitions["Spazer"]["C"] = "\x53\xef"
	item_definitions["Spazer"]["H"] = "\xa7\xef"

	# X-Ray
	item_definitions["XR"]["N"] = "\x0f\xef"
	item_definitions["XR"]["C"] = "\x63\xef"
	item_definitions["XR"]["H"] = "\xb7\xef"

	# Grapple Beam
	item_definitions["G"]["N"] = "\x17\xef"
	item_definitions["G"]["C"] = "\x6b\xef"
	item_definitions["G"]["H"] = "\xbf\xef"

	# Energy Tank
	item_definitions["E"]["N"] = "\xd7\xee"
	item_definitions["E"]["C"] = "\x2b\xef"
	item_definitions["E"]["H"] = "\x7f\xef"

	# Bombs
	item_definitions["B"]["N"] = "\xe7\xee"
	item_definitions["B"]["C"] = "\x3b\xef"
	item_definitions["B"]["H"] = "\x8f\xef"

	# Power Bombs
	item_definitions["PB"]["N"] = "\xe3\xee"
	item_definitions["PB"]["C"] = "\x37\xef"
	item_definitions["PB"]["H"] = "\x8b\xef"

	# Hi Jump
	item_definitions["HJ"]["N"] = "\xf3\xee"
	item_definitions["HJ"]["C"] = "\x47\xef"
	item_definitions["HJ"]["H"] = "\x9b\xef"

	# Space Jump
	item_definitions["SJ"]["N"] = "\x1b\xef"
	item_definitions["SJ"]["C"] = "\x6f\xef"
	item_definitions["SJ"]["H"] = "\xc3\xef"

	# Speed Booster
	item_definitions["SB"]["N"] = "\xf7\xee"
	item_definitions["SB"]["C"] = "\x4b\xef"
	item_definitions["SB"]["H"] = "\x9f\xef"

	# Spring Ball - Best item in the game
	item_definitions["SPB"]["N"] = "\x03\xef"
	item_definitions["SPB"]["C"] = "\x57\xef"
	item_definitions["SPB"]["H"] = "\xab\xef"

	# Varia Suit
	item_definitions["V"]["N"] = "\x07\xef"
	item_definitions["V"]["C"] = "\x5b\xef"
	item_definitions["V"]["H"] = "\xaf\xef"

	# Gravity Suit
	item_definitions["GS"]["N"] = "\x0b\xef"
	item_definitions["GS"]["C"] = "\x5f\xef"
	item_definitions["GS"]["H"] = "\xb3\xef"

	# Morph Ball
	item_definitions["MB"]["N"] = "\x23\xef"
	item_definitions["MB"]["C"] = "\x77\xef"
	item_definitions["MB"]["H"] = "\xcb\xef"

	# Reserve Tank
	item_definitions["RT"]["N"] = "\x27\xef"
	item_definitions["RT"]["C"] = "\x7b\xef"
	item_definitions["RT"]["H"] = "\xcf\xef"

	# Screw Attack
	item_definitions["SA"]["N"] = "\x1f\xef"
	item_definitions["SA"]["C"] = "\x73\xef"
	item_definitions["SA"]["H"] = "\xc7\xef"

	return item_definitions