# Author - Ross Mawhorter
# MinSetSet - used for keeping track of a set of minimal sets of items.
# I expect items to be denoted as strings, but really you can use whatever you
# want, as long as it's hashable.
# A + B will OR the two sets together. The resulting MinSetSet requires any of the
# item sets from either the first or the second item set
# A * B will AND the two sets together. The resulting MinSetSet requires all of the
# items from any set in A, and all of the items from any set in B
class MinSetSet:

	def __init__(self, set_list=None):
		if set_list is None:
			self.sets = [set()]
		else:
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
