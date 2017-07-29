# Ross Mawhorter
# test function for the constraints parser
# make sure there's no assertion errors!

import constraints

if __name__ == "__main__":

	#print constraints.find_expressions("| (& A B) C")
	
	print "test 1 - start"
	minset = constraints.parse_constraint("| (& A B) C")
	print minset
	assert not minset.matches(set(["A"]))
	assert not minset.matches(set(["B"]))
	assert minset.matches(set(["A", "B"]))
	assert minset.matches(set(["C"]))
	print "test 1 - success\n"

	print "test 2 - start"
	minset = constraints.parse_constraint("& A B")
	print minset
	assert not minset.matches(set(["C"]))
	assert minset.matches(set(["A", "B"]))
	print "test 2 - success\n"

	print "test 3 - start"
	minset = constraints.parse_constraint("& (| (| A B) (& C D)) (& (| E F) G)")
	print minset
	assert not minset.matches(set(["A", "B", "C", "D", "E", "F"]))
	assert minset.matches(set(["A", "E", "G"]))
	assert minset.matches(set(["B", "F", "G"]))
	assert minset.matches(set(["C", "D", "F", "G"]))
	print "test 3 - success\n"
	
	print "all tests - success"