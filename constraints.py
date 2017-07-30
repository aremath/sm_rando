# Ross Mawhorter
# Creates a MinSetSet from a constraint.
# Expects constraints with the following recursive syntax:
# Symbol () () ...
# A			requires A
# & A B C	requires all of A, B, C
# | A B C	requires any of A, B, C
# where () denotes a constraint surrounded by parens
# NOT IMPLEMENTED - 
# !()		Logical NOT of the expression
# the reason for this is evident in the structure of Super Metroid - since you
# can always turn every item off, there is no reason for an edge to ever require
# you not to have an item.

from minsetset import *

def parse_constraint(constraint):
	# BASE CASE
	# if it's not a symbol, then it's a variable
	if constraint[0] != "|" and constraint[0] != "&":
		return MinSetSet([set(constraint)])
	# RECURSIVE CASE
	else:
		symbol = constraint[0]
		# remove the symbol and the space, then find the top-level expressions
		constraint_list = find_expressions(constraint[2:])
		# now that constraint_list has every top-level expression, parse it recursively!
		minset_list = [parse_constraint(i) for i in constraint_list]
		# now combine them with either AND or OR
		if symbol == "|":
			return reduce(lambda x,y: x + y, minset_list)
		elif symbol == "&":
			return reduce(lambda x,y: x * y, minset_list)

def find_expressions(expr_str):
	"""Helper function for parse_constraint. Breaks a string up into a list. The
	elements of the list are the elements of the string separated by spaces, but
	ignoring spaces between parentheses"""
	expressions = []
	paren_count = 0
	accumulate = ""

	for char in expr_str:
		# If we're at the top level, break at spaces
		if paren_count == 0 and char == " ":
			expressions.append(accumulate)
			accumulate = ""
			continue
		if char == "(":
			paren_count += 1
			# the first paren delimits the expression, it isn't part of it
			if paren_count == 1:
				continue
		elif char == ")":
			paren_count -= 1
			# same with the last paren
			if paren_count == 0:
				continue
		# add the character if it wasn't a special-case
		accumulate += char
	# make sure the number of each type of paren matched
	assert paren_count == 0, expr_str
	# add the rest before the end of the string
	expressions.append(accumulate)
	return expressions
