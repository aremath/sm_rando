# Level as a numpy array of enum ints

class LevelState(object):
    """
    Composable structure that keeps track of level data.
    """

    def __init__(self, level, max_size=None):
        self.level = level
        self.max_size = max_size

    def add(self, other, offset):
        # Vector pointing to the new origin from the old origin
        new_origin = min(offset, (0,0)) # pointwise
        # Points from the new origin to the origin of the original frame
        self_offset = -new_origin
        # Points from the new origin to the origin of the added frame
        other_offset = self_offset + offset
        # Size should be a vector that points from the origin (0,0) to the point past the bottom right corner
        self_size = self_offset + self.size
        other_size = other_offset + other.size
        # The size of the new frame
        new_size = max(self_size, other_size) # pointwise
        new_max_size = min(self.max_size, other.max_size) # pointwise
        assert new_size <= new_max_size # pointwise
        # Allocate the new frame
        new_level = np.zeros(new_size)
        #TODO: implement update
        #update may need access to the scan direction...
        #TODO: it may not make sense to update a level separately from the rest of the samus state
        update(new_level, self.level, self_offset)
        update(new_level, other.level, other_offset)
        return LevelState(new_level, new_max_size)

    def copy(self):
        pass

class SamusState(object):

    def __init__(self, position, vertical_speed, horizontal_speed, items):
        self.position = position
        self.vertical_speed = vertical_speed
        self.horizontal_speed = horizontal_speed
        self.items = items

    def __geq__(self, other):
        p = self.position == other.position
        vv = self.vertical_speed == other.vertical_speed
        vh = self.horizontal_speed >= other.horizontal_speed
        i = self.items >= other.items
        return p and vv and vh and i

    def copy(self):
        pass

class SearchState(object):

    def __init__(self, samus, level):
        self.samus = samus
        self.level = level

    # Apply a rule to reach a new search state
    def apply_rule(self, rule):
        if self.samus >= rule.before_state.samus:
            # Try to add the rule to the current level
            n_changed, new_state = self.level.apply_rule(rule)
            if new_level is None:
                return None
            else:
                return new_state
        # Impossible to apply rule if Samus does not meet certain requirements
        else:
            return None

class Rule(object):

    def __init__(self, before_state, after_state, base_cost, extra_costs = None):
        self.before_state = before_state
        self.after_state = after_state
        self.base_cost = base_cost
        if extra_costs is None:
            self.extra_costs = []
        else:
            self.extra_costs = extra_costs

    @property
    def cost(self):
        return self.base_cost + sum(self.extra_costs)
    
    # Composes two Rules
    def __add__(self, other):
        before_state = self.before_state
        after_state = self.after_state + other.after_state
        #TODO: recompute offset
        #TODO: check compatibility of self.after with other.before
        #TODO: compute levels
        #TODO: discounting scheme
        base_cost = self.base_cost + other.base_cost
        extra_costs = self.extra_costs + other.extra_costs
        return Rule(before_state, after_state, base_cost, extra_costs)
