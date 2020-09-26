from functools import total_ordering
from collections import namedtuple

Coord = namedtuple("Coord", ("x", "y"))

@total_ordering
class Coord(tuple):
    """ Two-dimensional coordinate data type."""
    
    #def __init__(self, x, y):
    #    self.x = x
    #    self.y = y
    def __new__(self, x, y):
        return tuple.__new__(Coord, (x, y))
    
    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    def __add__(self, other):
        return Coord(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Coord(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Coord(self.x * other.x, self.y * other.y)

    def up(self):
        return Coord(self.x, self.y - 1)

    def right(self):
        return Coord(self.x + 1, self.y)

    def down(self):
        return Coord(self.x, self.y + 1)

    def left(self):
        return Coord(self.x - 1, self.y)

    def neighbors(self):
        return self.left(), self.up(), self.right(), self.down()

    def adjacent(self, other):
        return (other in self.neighbors())

    def to_tuple(self):
        return (self.x, self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash(self.to_tuple())

    def euclidean(self, other):
        return ((self.x-other.x)**2 + (self.y-other.y)**2)**(0.5)

    def __repr__(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"

    # Breaks priority ties
    # Uppermost leftmost tile is smallest
    def __lt__(self, other):
        if self.y < other.y:
            return True
        elif self.y == other.y:
            return self.x < other.x
        else:
            return False

    def __leq__(self, other):
        return self.y <= other.y and self.x <= other.x

    def __len__(self):
        return 2

    def scale(self, scale_factor):
        """ Multiply vector by scalar """
        return Coord(scale_factor*self.x, scale_factor*self.y)

    def to_unit(self):
        magnitude = self.euclidean(Coord(0,0))
        return self.scale(1/magnitude)

    def resolve_int(self):
        return Coord(int(self.x), int(self.y))

    def wall_relate(self, other):
        if other == self.up():
            return "U"
        elif other == self.left():
            return "L"
        elif other == self.right():
            return "R"
        elif other == self.down():
            return "D"
        else:
            assert False, "No wall_relate"

    def in_bounds(self, lower, upper):
        """Is this Coord inside the rectangle described by lower, upper?
        Like range, this includes the lower bound but not the upper bound. """
        return (self.x >= lower.x) and (self.y >= lower.y) and (self.x < upper.x) and (self.y < upper.y)

    def truncate(self, lower, upper):
        """Returns the tile inside the (lower,upper) rectangle closest to
        self."""
        new_x = self.x
        new_y = self.y
        if self.x < lower.x:
            new_x = lower.x
        elif self.x >= upper.x:
            new_x = upper.x - 1
        if self.y < lower.y:
            new_y = lower.y
        elif self.y >= upper.y:
            new_y = upper.y - 1
        return Coord(new_x, new_y)

    def area(self):
        return self.x * self.y

    def __neg__(self):
        return Coord(-1, -1) * self

    def abs(self):
        return Coord(abs(self.x), abs(self.y))

    def index(self, direction):
        if direction == Coord(1, 0):
            return self.x
        elif direction == Coord(0, 1):
            return self.y
        else:
            assert False, "Bad direction"

    def flip_in_rect(self, rect, axis):
        """ Find the position of self mirrored on axis within a rectangle. """
        # Relative distance within the rectangle
        self_index = self.index(axis) - rect.start.index(axis)
        # Maximum within the rectangle
        max_index = rect.end.index(axis) - 1
        self_index = self.index(axis)
        new_index = max_index - self.index(axis)
        # Perpendicular
        p = Coord(1,1) - axis
        return axis.scale(new_index) + self * p

    def pointwise_min(self, other):
        return Coord(min(self.x, other.x), min(self.y, other.y))

    def pointwise_max(self, other):
        return Coord(max(self.x, other.x), max(self.y, other.y))

    def sign(self):
        if self.x >= 0:
            x = 1
        elif self.x < 0:
            x = -1
        if self.y >= 0:
            y = 1
        elif self.y < 0:
            y = -1
        return Coord(x, y)

    def copy(self):
        return Coord(self.x, self.y)


class Rect(object):
    """ Two-dimensional rectangle data type. """

    def __init__(self, c1, c2):
        assert c2.x > c1.x
        assert c2.y > c1.y
        self.start = c1
        self.end = c2

    def __repr__(self):
        return "(" + str(self.start) + "," + str(self.end) + ")"

    def __iter__(self):
        for x in range(self.start.x, self.end.x):
            for y in range(self.start.y, self.end.y):
                yield Coord(x,y)

    def as_set(self):
        s = set()
        for x in range(self.start.x, self.end.x):
            for y in range(self.start.y, self.end.y):
                s.add(Coord(x,y))
        return s

    def as_list(self):
        l = []
        for x in range(self.start.x, self.end.x):
            for y in range(self.start.y, self.end.y):
                l.append(Coord(x,y))
        return l

    #TODO BUG: sometimes not within bounds...
    def split(self, index, direction):
        div_point = self.start + direction.scale(index)
        assert self.coord_within(div_point), div_point
        rect1 = Rect(self.start, div_point + (Coord(1,1) - direction) * (self.end - self.start))
        rect2 = Rect(div_point, self.end)
        return rect1, rect2

    def intersects(self, other):
        """Does self intersect with other?"""
        # self starts to the right of other
        if self.start.x >= other.end.x:
            return False
        # self ends to the left of other
        elif self.end.x <= other.start.x:
            return False
        # self starts below other
        elif self.start.y >= other.end.y:
            return False
        # self ends above other
        elif self.end.y <= other.start.y:
            return False
        else:
            return True

    def coord_within(self, c):
        """Is the given coordinate within self?"""
        if c.x >= self.start.x and c.x < self.end.x:
            if c.y >= self.start.y and c.y < self.end.y:
                return True
        return False

    def within(self, other):
        """Is self inside other?"""
        # Start and end must be within...
        # Subtract 1 from end because the bottommost rightmost square is one square up and to the left
        # of self.end
        return other.coord_within(self.start) and other.coord_within(self.end - Coord(1,1))

    def scale(self, factor):
        return Rect(self.start.scale(factor), self.end.scale(factor))

    def translate(self, c):
        return Rect(self.start + c, self.end + c)

    def area(self):
        return (self.end.x - self.start.x) * (self.end.y - self.start.y)

    def perimeter(self):
        return 2 * (self.end.x - self.start.x + self.end.y - self.start.y)

    def size_coord(self):
        return self.end - self.start

    def size(self, direction):
        return self.end.index(direction) - self.start.index(direction)

    def cut(self, other, axis, min_size):
        """Cuts self into up to two rectangles that do not overlap with other on the given axis.
        Rectangles resulting from the cut that are smaller than min_size will not be returned."""
        out = []
        r1_size = other.start.index(axis) - self.start.index(axis)
        r2_size = self.end.index(axis) - other.end.index(axis)
        if r1_size > 0 and r1_size >= min_size:
            r1 = Rect(self.start, self.end + (self.end - other.start) * axis)
            out.append(r1)
        if r2_size > 0 and r2_size >= min_size:
            r2 = Rect(self.start + (other.end - self.start) * axis, self.end)
            out.append(r2)
        return out

    def borders(self):
        """Returns a list of rectangles with directions that correspond to the four areas
        directly adjacent to the edges of self."""
        out = []
        l = Coord(-1,0)
        r = Coord(1,0)
        u = Coord(-1,0)
        d = Coord(1,0)
        for direction in [l,u]:
            p = Coord(1,1) - direction.abs()
            s = self.start + direction
            e = self.start + (self.end - self.start) * p
            rect = Rect(s, e)
            out.append((rect, direction))
        for direction in [r,d]:
            rect = Rect(self.start + (self.end - self.start) * direction, self.end + direction)
            out.append((rect, direction))
        return out

    # If self is a rectangle that lies within rect, this
    # returns a new rectangle which represents the new position after
    # flipping the containing rectangle across axis.
    def flip_in_rect(self, rect, axis):
        start_flip = self.start.flip_in_rect(rect, axis)
        end_flip = (self.end - Coord(1,1)).flip_in_rect(rect, axis)
        p = Coord(1,1) - axis
        other_start = end_flip * axis + start_flip * p
        other_end = end_flip * p + start_flip * axis
        other_end = other_end + Coord(1,1)
        return Rect(other_start, other_end)

    def iter_direction(self, direction=Coord(1,1)):
        """
        Iterate over the internal cells in the given direction, y inner, x outer
        """
        size = self.size_coord()
        if direction.x == 1:
            xoffset = 0
        else:
            xoffset = size.x - 1
        if direction.y == 1:
            yoffset = 0
        else:
            yoffset = size.y - 1
        offset = Coord(xoffset, yoffset)
        for x in range(0, size.x):
            for y in range(0, size.y):
                xy = Coord(x, y)
                yield xy * direction + offset

    def containing_rect(self, other):
        """
        Smallest rectangle that contains both self and other
        """
        new_start = self.start.pointwise_min(other.start)
        new_end = self.end.pointwise_max(other.end)
        return Rect(new_start, new_end)

    def copy(self):
        return Rect(self.start.copy(), self.end.copy())

