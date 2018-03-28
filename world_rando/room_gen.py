# code for generating the concrete room

#
def miniroom_partition(room_def, max_parts):
    """Creates a partition of the room into minirooms.
    The partition is a list of sets of xy values that index
    into the room dictionary."""
    #TODO: a list of xys isn't that useful to know the min and the max...
    while True:
        # choose a partition to subdivide
        # choose an x or a y to subdivide it at
        # break if the xy is invalid
        #   - causes a partition area to be too small
        #   - goes through an obstacle like a door
        #   - creates a partition over the max
        break
    pass
