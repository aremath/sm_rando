from .address import Address
from encoding import free_space

class AllocationError(Exception):
    pass

class Extent(object):
    """ extents describe free space by having a start place and a size """

    def __init__(self, start, size):
        self.start = start # the beginning address of the extent
        self.size = size   # how many bytes in the extent
        self.__check_valid()

    def __check_valid(self):
        assert(isinstance(self.start, Address))
        assert(self.size > 0)

    def __repr__(self):
        return '($'+str(self.start)+ ', '+hex(self.size)+')'

    def __gt__(self, e2):
        return self.start > e2.start

    def claim_space(self, size):
        assert(size > 0)
        assert(size <= self.size)
        addr = self.start
        to_delete = False
        if size == self.size:
            self.size = 0
            to_delete = True
        else:
            self.start = self.start.copy_increment(size)
            self.size -= size
        return addr, to_delete

    def has_space(self, size):
        assert(size > 0)
        return (size <= self.size)

    def exact_space(self, size):
        assert(size > 0)
        return (size == self.size)

    def get_addr(self):
        return self.start

    @property
    def end(self):
        return self.start + Address(self.size-1)

#TODO: maintain the invariant that extents are ordered by start address?
# - makes it easy to check if there are overlapping extents
class Bank(object):
    """A bank is a section of memory, some of which is free.
       this is stored as a list of extents"""

    def __init__(self, bank_n):
        self.bank = bank_n
        self.extent_list = []

    #TODO: assert no overlapping extents
    #TODO: merge adjacent extents
    def add_extent(self, extent):
        assert(isinstance(extent, Extent))
        assert extent.start.bank == self.bank
        bank2 = extent.end.bank
        assert bank2 == self.bank, "{} does not match {}".format(bank, bank2)
        self.extent_list.append(extent)

    def __repr__(self):
        return f"{hex(self.bank)}: {str(self.extent_list)}"

    #TODO: can use a fancier algorithm to decide where to find the space...
    def get_place(self, size):
        """
        Use first fit to find a place for the data
        """
        assert(size > 0)
        if len(self.extent_list) == 0:
            raise AllocationError
        addr = None
        remove = None
        for (i, extent) in enumerate(self.extent_list):
            # Use the first extent with enough space
            if extent.has_space(size):
                addr, to_delete = extent.claim_space(size)
                # If the extent has zero bytes left after the allocation,
                # mark it for removal
                if to_delete:
                    remove = i
                break
        # If this allocation resulted in an empty extent, remove it
        if remove is not None:
            self.extent_list.pop(remove)
        if addr is None:
            raise AllocationError
        else:
            return addr

    def mark_filled(self, address, size):
        new_extents = []
        for extent in self.extent_list:
            address_end = address + Address(size)
            extent_end = extent.start + Address(extent.size)
            # If it starts after or ends before, there's no intersection
            overlap_start = max(extent.start, address)
            overlap_end = min(extent_end, address_end)
            # No overlap
            if overlap_end <= overlap_start:
                new_extents.append(extent)
            else:
                if overlap_start > extent.start:
                    before = Extent(extent.start, int(address) - int(extent.start))
                    new_extents.append(before)
                if overlap_end < extent_end:
                    after = Extent(address_end, int(extent_end) - int(address_end))
                    new_extents.append(after)
        self.extent_list = new_extents

class Memory(object):

    def __init__(self, rom):
        self.rom = rom
        self.banks = {}
        # essentially a dictionary of banks!
        #TODO: what if the ROM is extended?
        for n in range(0x80, 0xdf + 1):
            self.banks[n] = Bank(n)

    def setup(self):
        """Sets up the memory with the default free space"""
        frees = free_space.find_free_space()
        for place, size in frees:
            addr = Address(place)
            self.mark_free(addr, size)

    def allocate(self, size, banks):
        """Try to allocate space for <data> in one of the given <banks>."""
        address = None
        assert len(banks) > 0
        banks = [self.banks[b] for b in banks]
        for bank in banks:
            try:
                address = bank.get_place(size)
            except AllocationError:
                continue
        # No place in any of the banks was found
        if address is None:
            raise AllocationError(f"No Memory Address could be found for {size} in {banks}")
        else:
            return address, bank

    def allocate_and_write(self, data, banks):
        """Try to allocate <data> in one of the <banks>, then
        write that data to the ROM."""
        size = len(data)
        address = self.allocate(size, banks)
        self.rom.write_to_new(address, data)
        return address

    def mark_free(self, address, size):
        """Marks a part of the rom as unallocated free space"""
        bank = address.bank
        # size-1 because size includes the byte at address
        # a 1-byte free space only refers to the byte at address
        #TODO: in the future, create multiple extents broken over the bank
        extent = Extent(address, size)
        self.banks[bank].add_extent(extent)

    def mark_filled(self, address, size):
        """Marks a part of the rom as allocated"""
        bank = address.bank
        self.banks[bank].mark_filled(address, size)

