# Ross Mawhorter
# Creates a function from a set of constraints
# Expects constraints with the following recursive syntax:
# () symbol ()
# !()		Logical NOT of the expression
# A			requires A
# & A B C	requires all of A, B, C
# | A B C	requires any of A, B, C
# where () denotes a constraint surrounded by parens

def parse_constraint_list(constraint_list, is_and=False):
	'''Takes a list of constraints and generates the corresponding function'''
	constraint_fns = [parse_constraint(constraint) for constraint in constraint_list]
	if is_and:
		return reduce(lambda x, y: lambda_and(x, y), constraint_fns)

	# assume OR
	else:
		return reduce(lambda x, y: lambda_or(x, y), constraint_fns)

def parse_constraint(constraints):
	'''Takes a set of constraints as a string and creates a lambda function'''

	# BASE CASE
	# if the constraint doesn't start with a parenthesis, then it's a list of necessary items
	if constraints[0] != "!" and constraints[0] != "(":

		# and them together
		if constraints[0] == "&":
			constraints = constraints[1:]
			items = set(constraints.split())
			return lambda x: items.issubset(x)

		# or them together
		elif constraints[0] == "|":
			constraints = constraints[1:]
			items = set(constraints.split())
			# if they have a nonempty intersection, they share an item...
			return lambda x: len(items.intersection(x)) != 0

		# a single item
		else:
			return lambda x: constraints in x

	# find LHS, symbol and RHS
	parencount = 0
	LHS = ""
	RHS = ""

	left_lambda, RH_constraints = parse_side(constraints)
	symbol = RH_constraints[1]
	# chop off space symbol space
	RH_constraints = RH_constraints[3:]
	right_lambda, _ = parse_side(RH_constraints)

	# return the final lambda
	if symbol == "|":
		return lambda_or(left_lambda, right_lambda)
	elif symbol == "&":
		return lambda_and(left_lambda, right_lambda)
	else:
		print "INVALID SYMBOL: ", symbol

def parse_side(constraints):
	'''Helper function for parse_constraints. Assuming constraints is of the
	form (1) s (2), returns a lambda for (1), and the rest of the constraints
	string "s (2)"'''

	# since we assume the form, we know it starts with (
	assert constraints[0] == "(" or constraints[0] == "!", constraints
	paren_count = 1
	is_not = False
	LHS = "("
	index = 1

	# check if we need to negate
	if constraints[0] == "!":
		is_not = True
		constraints = constraints[1:]

	# loop until we have satisfied all pairs of parens
	while paren_count != 0:
		if index == len(constraints):
			print "MALFORMED EXPRESSION: ", constraints
		LHS += constraints[index]
		if constraints[index] == "(": paren_count += 1
		if constraints[index] == ")": paren_count -= 1
		index += 1

	# chop LHS from constraints
	constraints = constraints[len(LHS):]

	# now LHS has the true leftmost side of the constraints, parse it
	# chop the outermost parens
	LHS = LHS[1:-1]

	# recursive call
	left_lambda = parse_constraint(LHS)
	# did we not it?
	if is_not:
		return lambda_not(left_lambda), constraints
	else:
		return left_lambda, constraints

# every edge has a lambda function which takes an items dictionary
# and returns whether that items dictionary will allow traversal of
# that edge

def lambda_and(lambda1, lambda2):
	'''Returns a function which ands the results of lambda1 and lambda2'''
	return lambda x: lambda1(x) and lambda2(x)

def lambda_or(lambda1, lambda2):
	'''Returns a function which ors the results of lambda1 and lambda2'''
	return lambda x: lambda1(x) or lambda2(x)

def lambda_not(lambda1):
	'''Returns a function which nots lambda1'''
	return lambda x: not lambda1(x)

