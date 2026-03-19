import numpy as np

from world_rando.coord import *
from world_rando.room_perception.angleset import *

# Arbitrary constant to accommodate numerical errors in things that /should/ be equal but are not.
epsilon = 10**-10

# Find the angle (in radians) from the given pivot to the given point (assuming the x-axis is 0 radians)
def point_angle(pivot, point):
    # Determine the quadrant of the point
    x_offset = point.x - pivot.x
    y_offset = point.y - pivot.y
    x_nneg = x_offset > 0
    y_nneg = y_offset > 0
    # Special case for identical points
    if pivot == point:
        assert False, "Angle calculation impossible for overlapping points!"
    # Special case for points with the same x-coord
    if point.x == pivot.x:
        if y_nneg:
            return math.pi / 2
        else:
            return 3 * math.pi / 2
    # Special case for points with the same y-coord
    if point.y == pivot.y:
        if x_nneg:
            return 0
        else:
            return math.pi
    # Q1
    if x_nneg and y_nneg:
        #print("Q1")
        return math.atan(y_offset / x_offset)
    # Q2
    elif (not x_nneg) and y_nneg:
        #print("Q2")
        return math.pi / 2 + math.atan(-x_offset / y_offset)
    # Q3
    elif (not x_nneg) and (not y_nneg):
        #print("Q3")
        return math.pi + math.atan(-y_offset / -x_offset) # this is the same as Q1
    # Q4
    elif x_nneg and (not y_nneg):
        #print("Q4")
        return 3 * math.pi / 2 + math.atan(x_offset / -y_offset) # this is the same as Q2
    else:
        assert False, "Angle cases not exhaustive!"


# The corners of a coord
def coord_points(c):
    return [Coord(c.x, c.y), Coord(c.x + 1, c.y), Coord(c.x, c.y + 1), Coord(c.x + 1, c.y + 1)]

def coord_center(c):
    return Coord(c.x + 0.5, c.y + 0.5)

# Returns true iff point lies on the line that passes through both a and b
def point_on_line(point, line):
    a, b = line
    if a == b:
        assert False, "does not define a line!"
    return (b.x - a.x) * (point.y - a.y) == (point.x - a.x) * (b.y - a.y)

# Returns true iff point lies on the segment from a to b
def point_on_segment(point, segment):
    a, b = line
    # Point must be within the bounding box of the line segment
    minx = min(a.x, b.x)
    maxx = max(a.x, b.x)
    if point.x < minx or point.x > maxx:
        return False
    miny = min(a.y, b.y)
    maxy = max(a.y, b.y)
    if point.y < miny or point.y > maxy:
        return False
    return point_on_line(point, a, b)

# returns False if the point does not lie on the segment
# Otherwise, returns the t-value (progress along the segment)
def point_on_segment_t(point, line):
    # First, solve for t
    a, b = line
    # Line is defined by a + (b-a)*t
    # so a + (b-a)*t = p is a system of two equations
    # t = (p - a) / (b - a)
    if a.x != b.x:
        t = (point.x - a.x) / (b.x - a.x)
    elif a.y != b.y:
        t = (point.y - a.y) / (b.y - a.y)
    # This happens if a == b
    else:
        assert False, "does not define a line!"
    if t < 0 or t > 1:
        return False
    else:
        return t

def line_intersect(line1, line2):
    # line 1 = a1 + (a2 - a1) * t
    a1, a2 = line1
    # line 2 = b1 + (b2 - b1) * t
    b1, b2 = line2
    mat = np.array([
        [a2.x - a1.x, b1.x - b2.x], 
        [a2.y - a1.y, b1.y - b2.y]])
    #print(mat)
    # Solve a1 + (a2 - a1) * t1 = b1 + (b2 - b1) * t2 for t1, t2
    try:
        mat_inv = np.linalg.inv(mat)
        #print(mat_inv)
    # If the matrix is singular, then the lines are parallel
    except np.linalg.LinAlgError:
        # They could be on top of each other
        if point_on_line(a1, line2):
            return a1, None, True
        # Otherwise, these are parallel lines that do not intersect
        else:
            return None
    #print(b1 - a1)
    t = mat_inv @ (b1 - a1)
    #print(t)
    eq1 = a1 + (a2 - a1).scale(t[0])
    eq2 = b1 + (b2 - b1).scale(t[1])
    #assert eq1 == eq2, (eq1, eq2)
    assert abs(eq1.x - eq2.x) < epsilon, (eq1, eq2)
    assert abs(eq1.y - eq2.y) < epsilon, (eq1, eq2)
    return eq1, t, False

def line_segment_intersect(line1, line2):
    s = line_intersect(line1, line2)
    if s is None:
        return None
    else:
        p, t, same_line = s
        # If the lines are the same then they intersect iff (WLOG) one of the endpoints of a lies within b
        if same_line:
            a1, a2 = line1
            if point_on_line(a1, line2):
                return a1 # Among other points
            elif point_on_line(a2, line2):
                return a2
            # The lines are the same but the segments don't overlap
            else:
                return None
        # If the lines are not parallel, then they intersect at p
        else:
            # The segments intersect iff p is inside both of them
            if t[0] >= 0 and t[0] <= 1 and t[1] >= 0 and t[1] <= 1:
                return p
            else:
                return None

def line_segment_touches_xplus(segment):
    a, b = segment
    # It only crosses if one is above and the other is below
    if (a.y >= 0 and b.y <= 0) or (a.y <= 0 and b.y >= 0):
        # The line segment is coterminous with the x axis
        if a.y == b.y:
            return True
        # The line crosses the x-axis somewhere
        # Solve the y part of parametric equation [x, 0] = [b.x - a.x, b.y - a.y] * t + [a.x, a.y] for t:
        t = a.y / (a.y - b.y)
        # Substitute t back into the x part
        x = b.x * t - a.x * t + a.x
        # The line crosses at (x, 0)
        if x >= 0:
            return True
        else:
            return False
    else:
        return False

# OUTMODED because of the ambiguous case when a line starts on the x axis.
# However, still potentially useful for the case of an arbitrary line and not a segment
# If the line segment crosses the X+ axis, then the larger of the two angles is the clockwise start of the segment
# and the segment wraps around 0 radians
#if line_segment_touches_xplus((rel_a, rel_b)):

#TODO: if the pivot lies on the line defined by (a,b), then the interval occupied by the line is empty (or only contains one point?)
#TODO: what if a=b?
def line_segment_interval(pivot, line):
    point_a, point_b = line
    angle_a = point_angle(pivot, point_a)
    angle_b = point_angle(pivot, point_b)
    min_angle = min(angle_a, angle_b)
    max_angle = max(angle_a, angle_b)
    if (max_angle - min_angle) >= math.pi:
        i = Interval(max_angle, min_angle)
    else:
        i = Interval(min_angle, max_angle)
    # A line segment cannot take up half the field of view
    assert i.size < math.pi
    return i

# Find the vision angles that the visible surface of the given coordinate occupies when standing at the center of the pivot coord
# Any angle strictly within (start, end) will hit the square at c unless it hits something else first
#TODO: what about the endpoints?
def angle_interval(pivot, c):
    if pivot == c:
        assert False, "The angle interval for overlapping points is undefined!"
    center = coord_center(pivot)
    ps = coord_points(c)
    angles = [point_angle(center, p) for p in ps]
    #TODO this is wrong for intervals that straddle the x axis!
    start = min(angles)
    end = max(angles)
    return (start, end)

def angle_intersect(viewpoint, angle, segment):
    ray = (viewpoint, Coord(viewpoint.x + math.cos(angle), viewpoint.y + math.sin(angle)))
    i = line_intersect(ray, segment)
    #print(i)
    if i is None:
        return None
    else:
        p, t, same_line = i
        # If it actually hits the segment, return the intersection point
        if t[1] >= -epsilon or t[1] <= 1 + epsilon:
            return p
        else:
            return None

def segment_fraction(line, fraction):
    a,b = line
    rel_b = b - a
    return a + rel_b.scale(fraction)

# Returns true iff viewpoint is on the same side of line as point
# This is the same as saying that point is visible from viewpoint with respect to line
def point_infront(viewpoint, point, line):
    #TODO: what if viewpoint = point?
    #TODO: what if viewpoint is on line?
    #TODO: what if point is on line?
    ray = (viewpoint, point)
    i = line_intersect(ray, line)
    # Happens if viewpoint -> point is parallel to line. Unless viewpoint lies on line, point will always be on the same side as viewpoint
    if i is None:
        #print("Parallel View Ray")
        return True
    else:
        _, t, same_line = i
        if same_line:
            #print("Same View Ray")
            return True
        else:
            #print("Ray Intersects")
            #print(t, t[0] <= 0)
            #if t[0] <= 0 or t[0] >= 1
            if t[0] <= epsilon or t[0] >= 1-epsilon:
                return True
            else:
                return False

# Determine what part of line1 is visible from point if line2 is also present
def occlude(point, line1, line2):
    a1, a2 = line1
    b1, b2 = line2
    a1_infront = point_infront(point, a1, line2)
    #print(a1, a1_infront)
    a2_infront = point_infront(point, a2, line2)
    #print(a2, a2_infront)
    # If both a points are in front, then line1 is in front of line2, and no occlusion happens
    if a1_infront and a2_infront:
        #print("Both in front (Case 1)")
        return line_segment_interval(point, line1)
    # If both points are behind, then line2 occludes line1
    elif not a1_infront and not a2_infront:
        #print("Both behind (Case 2)")
        return line_segment_interval(point, line1) - line_segment_interval(point, line2)
    # If one is behind and the other is in front, then the lines line1 and line2 must intersect at some point p (though the segments may not intersect).
    # If we call the infront point I and the behind J, then [I, p] is always visible and [p, J] may be occluded by line2
    # The visible part of line1 is [I, p] u ([p, J] - line2)
    elif not a1_infront and a2_infront:
        infront = a2
        behind = a1
    elif a1_infront and not a2_infront:
        infront = a1
        behind = a2
    #print("One in front (Case 3)")
    intersect = line_intersect(line1, line2)
    #print(line1, line2)
    #print(intersect)
    assert len(intersect) == 3
    p, _, _ = intersect
    s1 = line_segment_interval(point, (infront, p))
    s2 = line_segment_interval(point, (p, behind))
    return s1 | (s2 - line_segment_interval(point, line2))
