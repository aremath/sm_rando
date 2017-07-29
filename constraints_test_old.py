# Ross Mawhorter
# test function for the constraints parser
# make sure there's no assertion errors!

import constraints

if __name__ == "__main__":
	lambda1 = constraints.parse_constraint("(& A B) & !(C)")
	assert lambda1(["C"]) == False
	assert lambda1(["A", "C"]) == False
	assert lambda1(["J", "D", "C"]) == False
	assert lambda1(["A", "B", "C"]) == False
	assert lambda1(["A"]) == False
	assert lambda1(["B"]) == False
	assert lambda1(["A", "B"]) == True

	lambda1 = constraints.parse_constraint("(A) & (B)")
	assert lambda1(["C"]) == False
	assert lambda1(["A", "B"]) == True

	lambda1 = constraints.parse_constraint("((| A B) | (& C D)) & ((| E F) & (G))")
	assert lambda1(["A", "B", "C", "D", "E", "F"]) == False
	assert lambda1(["A", "E", "G"]) == True
	assert lambda1(["B", "F", "G"]) == True
	assert lambda1(["C", "D", "F", "G"]) == True

	c_list = ["A", "| B C"]
	c_and = constraints.parse_constraint_list(c_list, True)
	c_or = constraints.parse_constraint_list(c_list, False)

	assert c_and(["A", "B"]) == True
	assert c_and(["C"]) == False

	assert c_or(["C"]) == True
	assert c_or(["A"]) == True

	print "SUCCESS"