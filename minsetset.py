from item_set import *
# Author - Aremath
# MinSetSet - used for keeping track of a set of minimal sets of items.
# I expect items to be denoted as strings, but really you can use whatever you
# want, as long as it's hashable.
# A + B will OR the two sets together. The resulting MinSetSet requires any of the
# item sets from either the first or the second item set
# A * B will AND the two sets together. The resulting MinSetSet requires all of the
# items from any set in A, and all of the items from any set in B
class MinSetSet:

	def __init__(self, set_=None):
		if set_ is None:
			self.sets = set(ItemSet())
		else:
			self.sets = set_

	def __add__(self, other):
		"""OR the two minsetsets together. Either you have a set from one,
		or a set from the other."""
		return MinSetSet(self.sets | other.sets)

	def __mul__(self, other):
		"""AND the two minsetsets together. Union all pairs, then filter. You 
		have one of the sets from one, and one from the other."""
		all_pairs = set()
		for self_set in self.sets:
			for other_set in other.sets:
				all_pairs.add(self_set | other_set)
		all_pairs_set = MinSetSet(all_pairs)
		return all_pairs_set

	def matches(self, items):
		"""Is items good enough to pass self? All sets in self are valid ways
		to pass. Is items a superset of any of them?"""
		for self_set in self.sets:
			if items >= self_set:
				return True
		return False

	def __repr__(self):
		self_str = "MinSS{"
		for self_set in self.sets:
			self_str += repr(self_set) + ", "
		# remove the trailing ", "
		return self_str[:-2] + "}"
