# Ross Mawhorter
# Creates a function from a set of constraints
# Expects constraints with the following recursive syntax:
# Symbol () () ...
# A			requires A
# & A B C	requires all of A, B, C
# | A B C	requires any of A, B, C
# where () denotes a constraint surrounded by parens
# NOT IMPLEMENTED - 
# !()		Logical NOT of the expression

class MinSetSet:

	def __init__(self):
		self.sets = [set()]

	def __init__(self, set_list):
		self.sets = set_list

	def _filter(self):
		"""Removes non-minimal elements"""
		new_sets = []
		for i_index, i_set in enumerate(self.sets):
			keep = True
			for u_index, u_set in enumerate(self.sets):
				if i_set >= u_set and i_index != u_index:
					keep = False
					break
			if keep:
				new_sets.append(i_set)
		self.sets = new_sets

	def __add__(self, other):
		"""OR the two minsetsets together. Either you have a set from one,
		or a set from the other."""
		both = []
		both.extend(self.sets)
		both.extend(other.sets)
		both_set = MinSetSet(both)
		both_set._filter()
		return both_set

	def __mul__(self, other):
		"""AND the two minsetsets together. Union all pairs, then filter. You 
		have one of the sets from one, and one from the other."""
		all_pairs = []
		for self_set in self.sets:
			for other_set in other.sets:
				all_pairs.append(self_set | other_set)
		all_pairs_set = MinSetSet(all_pairs)
		all_pairs_set._filter()
		return all_pairs_set

	def matches(self, items):
		"""Is items good enough to pass self? All sets in self are valid ways
		to pass. Is items a superset of any of them?"""
		for self_set in self.sets:
			if items >= self_set:
				return True
		return False

	def __repr__(self):
		self_str = ""
		for self_set in self.sets:
			self_str += repr(self_set) + "\n"
		# remove the trailing \n
		return self_str[:-1]


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
