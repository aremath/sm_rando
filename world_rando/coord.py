
class Coord(object):
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

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

    # stupid way to break priority ties
    # Uppermost leftmost tile is smallest
    def __lt__(self, other):
        if self.y < other.y:
            return True
        elif self.y == other.y:
            return self.x < other.x
        else:
            return False

    def scale(self, scale_factor):
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

    def neg(self):
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

class Rect(object):

    def __init__(self, c1, c2):
        assert c2.x > c1.x
        assert c2.y > c1.y
        self.start = c1
        self.end = c2

    def __repr__(self):
        return "(" + str(self.start) + "," + str(self.end) + ")"

    def as_set(self):
        s = set()
        for x in range(self.start.x, self.end.x):
            for y in range(self.start.y, self.end.y):
                s.add(Coord(x,y))
        return s

    # TODO: some way to to this with iterators so that I can do
    # " for c in rect: "
    def as_list(self):
        l = []
        for x in range(self.start.x, self.end.x):
            for y in range(self.start.y, self.end.y):
                l.append(Coord(x,y))
        return l

    def split(self, index, direction):
        div_point = self.start + direction.scale(index)
        assert self.coord_within(div_point)
        rect1 = Rect(self.start, div_point + (Coord(1,1) - direction) * rect.end)
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

    def size(self, direction):
        return self.end.index(direction) - self.start.index(direction)

    def flip(self, axis):
        flip = axis.scale(-1)
        p = Coord(1,1) - axis
        start_flip = self.start * flip
        end_flip = self.end * flip
        new_start_1 = end_flip.index(axis) + axis
        new_start_2 = start_flip.index(p)
        new_start = new_start_1 + new_start_2
        new_end_1 = start_flip.index(axis) + axis
        new_end_2 = end_flip.index(p)
        new_end = new_end_1 + new_end_2
        return Rect(new_start, new_end)



