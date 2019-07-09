# Author - Ross Mawhorter
# short test function for the constraints parser
# make sure there's no assertion errors!
# since it's just a few small examples, it's more of a sanity check than a real test

import constraints
from item_set import *

if __name__ == "__main__":

	print "test 1 - start"
	minset = constraints.parse_constraint("| (& G GS) CB")
	print minset
	assert not minset.matches(ItemSet(["G"]))
	assert not minset.matches(ItemSet(["GS"]))
	assert minset.matches(ItemSet(["G", "GS"]))
	assert minset.matches(ItemSet(["CB"]))
	print "test 1 - success\n"

	print "test 2 - start"
	minset = constraints.parse_constraint("& IB SB")
	print minset
	assert not minset.matches(ItemSet(["G"]))
	assert minset.matches(ItemSet(["IB", "SB"]))
	print "test 2 - success\n"

	print "test 3 - start"
	minset = constraints.parse_constraint("& (| (| Kraid Phantoon) (& Draygon Ridley)) (& (| Botwoon Spore_Spawn) Golden_Torizo)")
	print minset
	assert not minset.matches(ItemSet(["Kraid", "Phantoon", "Draygon", "Ridley", "Botwoon", "Spore_Spawn"]))
	assert minset.matches(ItemSet(["Kraid", "Botwoon", "Golden_Torizo"]))
	assert minset.matches(ItemSet(["Phantoon", "Spore_Spawn", "Golden_Torizo"]))
	assert minset.matches(ItemSet(["Draygon", "Ridley", "Spore_Spawn", "Golden_Torizo"]))
	print "test 3 - success\n"
	
	print "all tests - success"
