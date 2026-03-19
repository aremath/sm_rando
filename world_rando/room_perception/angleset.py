import math
from itertools import combinations
from abc import ABC, abstractmethod, abstractproperty

twopi = 2 * math.pi

# Angles are in [0, 2*pi) with angle 2*pi aliasing to 0
def angle_inbounds(angle):
    return angle >= 0 and angle < twopi

class AngleSetInterface(ABC):

    @abstractmethod
    def has(self, angle):
        pass

    @abstractmethod
    def overlaps(self, other):
        pass

    @abstractmethod
    def __or__(self, other):
        pass

    @abstractmethod
    def __and__(self, other):
        pass

    @abstractmethod
    def __sub__(self, other):
        pass

    @abstractmethod
    def copy(self):
        pass

    @abstractproperty
    def size(self):
        pass

def all_interval():
    i = Interval(0,0)
    i.special = True
    return i

def none_interval():
    return AngleSet([])

# Represents angle intervals
# start is an angle in [0, 2*pi)
# end is an angle in [0, 2*pi)
# (An interval of width zero means the object cannot be seen, or can only be seen by a single ray)

# Attempt to make an interval, but if the interval is singleton, make an empty set instead
# Useful for intersections that overlap on the boundaries
def mk_nonsingle_interval(start, end):
    if start == end:
        return AngleSet([])
    return Interval(start, end)

#TODO: what if a singleton set is attempted to be created? (e.g. by intersecting two intervals that share one point?)
class Interval(AngleSetInterface):

    pure = True
    
    def __init__(self, start, end):
        assert angle_inbounds(start)
        assert angle_inbounds(end)
        self.start = start
        self.end = end
        # An interval where start == end and special == False represents a single visible point
        # This is commonly the case when viewing the end of a segment, for example
        #assert start != end, "NoneInterval created!"
        # start > end iff the interval crosses 0 radians and wraps back around
        self.special = self.start > self.end
        if self.special:
            # The true end is an angle >= 2*pi
            self.width = self.end + twopi - self.start
        else:
            self.width = self.end - self.start
        assert angle_inbounds(self.width)

    # Checks if this interval contains the given angle (inclusive)
    def has(self, angle):
        assert angle_inbounds(angle)
        if self.special:
            # The angle is between twopi and the actual start
            if angle >= self.start:
                return True
            # angle is between 0 and aliased end
            elif angle <= self.end:
                return True
            else:
                return False
        else:
            return angle >= self.start and angle <= self.end

    def overlaps(self, other):
        if not other.pure:
            promote = AngleSet([self])
            return promote.overlaps(other)
        return (self.has(other.start) or self.has(other.end)) or (other.has(self.start) or other.has(self.start))

    # Returns true iff self wraps around other so that the clockwise order is:
    # other.start, self.end, self.start, other.end
    def wraps_around(self, other):
        #TODO: this is also true iff self.has(other.start) or self.has(other.end) (unless the two sets are coterminous...)
        if other.has(self.start) and other.has(self.end):
            # Special case for singleton sets, which never wrap around
            if self.start == self.end and not self.special:
                return False
            i = Interval(other.start, self.start)
            return i.has(self.end)
        else:
            return False

    # Union
    def __or__(self, other):
        if not other.pure:
            promote = AngleSet([self])
            return promote | other
        # If the endpoints of the other interval are inside of self, then 
        if self.has(other.start) and self.has(other.end):
            # One of two cases:
            # 1. other is contained within self: SS OS OE SE (clockwise)
            # 2. other wraps around self: SS OE OS SE (clockwise)
            if other.wraps_around(self):
                return all_interval() #TODO: this is problematic if we allow other.start = other.end to represent singleton sets
            else:
                return self.copy()
        elif self.has(other.start):
            return Interval(self.start, other.end)
        elif self.has(other.end):
            return Interval(other.start, self.end)
        # If other.has(self.start) but !other.has(self.end) then self.has(other.end), so this case is already covered
        elif other.has(self.start) and other.has(self.end):
            if self.wraps_around(other):
                return all_interval()
            else:
                return self.copy()
        # If they are not overlapping, make an angleset that includes both
        else:
            return AngleSet([self.copy(), other.copy()])            

    # Intersection
    def __and__(self, other):
        if not other.pure:
            promote = AngleSet([self])
            return promote & other
        if self.has(other.start) and self.has(other.end):
            # This is analagous to the union operation
            # other splits self into two parts if it wraps around
            if other.wraps_around(self):
                # This happens if other is an AllInterval
                if other.end == other.start:
                    return self.copy()
                # This happens iff self is an AllInterval
                elif self.end == self.start:
                    return other.copy()
                else:
                    return AngleSet([mk_nonsingle_interval(self.start, other.end), mk_nonsingle_interval(other.start, self.end)])
            else:
                return other.copy()
        elif self.has(other.start):
            return mk_nonsingle_interval(other.start, self.end)
        elif self.has(other.end):
            return mk_nonsingle_interval(self.start, other.end)
        elif other.has(self.start) and other.has(self.end):
            # self wraps around
            if self.wraps_around(other):
                if self.end == self.start:
                    return other.copy()
                elif other.end == other.start:
                    return self.copy()
                else:
                    return AngleSet([mk_nonsingle_interval(other.start, self.end), mk_nonsingle_interval(self.start, other.end)])
            else:
                return self.copy()
        # If they are not overlapping, the intersection is empty
        else:
            return none_interval()

    # Setminus
    def __sub__(self, other):
        if not other.pure:
            promote = AngleSet([self])
            return promote - other
        if self.has(other.start) and self.has(other.end):
            # If it wraps around, then only the area between the wrap around is preserved
            if other.wraps_around(self):
                if other.end == other.start:
                    return none_interval()
                else:
                    #TODO: this nonsingle is redunant with the previous check
                    return mk_nonsingle_interval(other.end, other.start)
            # If it doesn't wrap around, then it splits self into two regions
            else:
                return AngleSet([Interval(self.start, other.start), Interval(other.end, self.end)])
        elif self.has(other.start):
            return mk_nonsingle_interval(self.start, other.start)
        elif self.has(other.end):
            return mk_nonsingle_interval(other.end, self.end)
        #TODO: sub is not symmetric, so check this!
        elif other.has(self.start) and other.has(self.end):
            # If other is an allinterval then everything is removed
            if other.start == other.end:
                return none_interval()
            elif self.wraps_around(other):
                return mk_nonsingle_interval(other.end, other.start)
            # If self does not wrap around, then it is contained within other and everything is removed
            else:
                return none_interval()
        # If they are not overlapping, nothing is removed
        else:
            return self.copy()

    def copy(self):
        return Interval(self.start, self.end)

    @property
    def size(self):
        s = self.end - self.start
        if self.special:
            return s + twopi
        else:
            return s

    def __repr__(self):
        return f"Interval({self.start}, {self.end})"

#TODO: Rename to IntervalSet?
#TODO: possible performance improvement:
# Require angles to be ordered by clockwise start so that we can determine quickly where they interact
# Represents a set of angles as zero or more non-overlappng intervals
class AngleSet(AngleSetInterface):

    pure = False

    def __init__(self, intervals):
        self.intervals = []
        for i in intervals:
            self.add_interval(i)
        assert len(self.check_overlap()) == 0

    def has(self, angle):
        return any([i.has(angle) for i in self.intervals])

    def overlaps_interval(self, interval):
        return any([i.overlaps(interval) for i in self.intervals])

    # Check all n^2 interval pairs for overlap
    def overlaps(self, other):
        return any([self.overlaps_interval(i) for i in other.intervals])

    def check_overlap(self):
        overlaps = []
        for i,j in combinations(self.intervals, 2):
            if i.overlaps(j):
                overlaps.append((i,j))
        return overlaps

    #TODO: the way this is implemented means it takes n^2 time to build an AngleSet with n angles
    def add_interval(self, add_i):
        assert add_i.pure, add_i
        overlaps = []
        non_overlaps = []
        for i in self.intervals:
            # If the intervals overlap then adding the interval alters the interval
            if i.overlaps(add_i):
                overlaps.append(i)
            else:
                non_overlaps.append(i)
        base = add_i
        # The intervals are non-overlapping:
        # Any interval that does not overlap with add also does not overlap with add | o forall o
        for o in overlaps:
            base |= o
            assert base.pure
        self.intervals = non_overlaps + [base]

    def intersect_interval(self, int_i):
        assert int_i.pure, int_i
        overlaps = []
        for i in self.intervals:
            if i.overlaps(int_i):
                overlaps.append(i)
        #print("Overlaps: ", overlaps)
        # Intersection of the union is the union of the intersections
        # Intersections are mutually disjoint because they are smaller than the original (disjoint) sets
        new_intervals = []
        for o in overlaps:
            new_i = o & int_i
            if new_i.pure:
                new_intervals.append(new_i)
            else:
                new_intervals.extend(new_i.intervals)
        self.intervals = new_intervals

    def subtract_interval(self, sub_i):
        assert sub_i.pure, sub_i
        overlaps = []
        non_overlaps = []
        for i in self.intervals:
            if i.overlaps(sub_i):
                overlaps.append(i)
            else:
                non_overlaps.append(i)
        new_intervals = []
        for o in overlaps:
            new_i = o - sub_i
            if new_i.pure:
                new_intervals.append(new_i)
            else:
                new_intervals.extend(new_i.intervals)
        self.intervals = non_overlaps + new_intervals

    # Union
    #TODO what if "self" is not pure?
    def __or__(self, other):
        ss = self.copy()
        if other.pure:
            ss.add_interval(other)
            return ss
        for i in other.intervals:
            ss.add_interval(i)
        return ss

    # Intersection
    def __and__(self, other):
        if other.pure:
            ss = self.copy()
            ss.intersect_interval(other)
            return ss
        # Intersection of the union is the union of the intersection
        #TODO: it seems extremely inefficient to copy self so many times...
        base = AngleSet([])
        for i in other.intervals:
            ss = self.copy()
            ss.intersect_interval(i)
            base = base | ss
        return base

    # Removes other from self, creating a new AngleSet
    def __sub__(self, other):
        ss = self.copy()
        if other.pure:
            ss.subtract_interval(other)
            return ss
        for i in other.intervals:
            ss.subtract_interval(i)
        return ss

    @property
    def size(self):
        size = 0
        for i in self.intervals:
            size += i.size
        assert size <= twopi
        return size

    def copy(self):
        return AngleSet([i.copy() for i in self.intervals])

    def __repr__(self):
        return f"AngleSet({self.intervals.__repr__()})"