
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

def xy_set(dim1, dim2):
    """Creates a set of the coordinates in the rectangle defined by dim1, dim2."""
    xys = set()
    for x in range(dim1.x, dim2.x):
        for y in range(dim1.y, dim2.y):
            xys.add(Coord(x,y)
    return xys

def split_rect(rect, index, direction):
    """Returns two new rectangles from splitting the rectangle along index."""
    div_point = rect[0] + direction.scale(index)
    rect1 = (rect[0], div_point + (Coord(1,1) - direction) * rect[1])
    rect2 = (div_point, rect[1])
    return rect1, rect2
    
