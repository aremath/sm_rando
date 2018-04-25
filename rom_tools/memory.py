from address import Address


class Extent(object):
    """ extents describe free space by having a start place and a size """
    def __init__(self, start, size):
        self.start = start # the beginning address of the extent
        self.size = size   # how many bytes in the extent
        self.__check_valid()

    def __check_valid(self):
        assert(isinstance(start, Address))
        assert(self.size > 0)

    def claim_space(self, size):
        assert(size > 0)
        assert(size <= self.size)
        if size == self.size:
            self.size = 0
            return None
        else:
            self.start = self.start.copy_increment(size)
            self.size -= size
            return self
    def has_space(self, size):
        assert(size > 0)
        return (size <= self.size)

    def get_addr(self):
        return self.start

class Bank(object):
    """docstring for Bank."""
    def __init__(self):
        self.extent_list = []

    def insert_extent(self, extent):
        assert(isinstance(extent, Extent))
        self.extent_list.append(extent)

    def get_place(self, size):
        assert(size > 0)
        assert(len(self.extent_list) != 0)
        for i in range(len(self.extent_list)):
            if self.extent_list[i].has_space(size):
                ex = self.extent_list.pop(i)
                replace = ex.claim_space(size)
                if replace is not None:
                    self.extent_list.append(replace)
                return ex.get_addr()
        print("Unable to find enough space for your request")
        assert(False)
