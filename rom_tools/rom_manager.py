from . import level
import subprocess
from . import areamap
from .memory import *
from .address import Address
from shutil import copy2 as copy_file
from hashlib import md5
from os import stat, remove, rename
from . import byte_ops

def _checksum(filename):
    """ md5sums a file """
    with open(filename, 'rb') as file:
        m = md5()
        while True:
            data = file.read(4048)
            if not data:
                break
            m.update(data)
    return m.hexdigest()

def _file_length(filename):
    statinfo = stat(filename)
    return statinfo.st_size

class RomManager(object):
    """The Rom Manager handles the actual byte facing aspects of the rom editing
       Can be used to both read and write to the rom, also contains meta data
       to make inserting rooms and room headers easier.
       Also *eventually* will be able to detect if your rom is `pure` and apply
       some necessary patches auto-magically"""

    def __init__(self,clean_name,new_name):
        assert clean_name != new_name, "The new rom name cannot be the same as the clean rom name!"
        #TODO: assert that clean_name refers to an actual file,
        # and that new_name does not refer to an existing file
        self.load_rom(clean_name, new_name)
        # Create a memory model for the new ROM
        self.memory = Memory(self)
        self.memory.setup()

    def load_rom(self, clean_name, new_name):
        """Opens the files associated with the clean rom and the modded rom"""

        pure_rom_sum = '21f3e98df4780ee1c667b84e57d88675'
        modded_rom_sum = 'idk'
        pure_rom_size = 3145728

        # First, make a copy of clean_name as new_name
        copy_file(clean_name, new_name)

        checksum = _checksum(new_name)
        filesize = _file_length(new_name)
        # TODO: Check and decapitate...
        # But what to do with the clean one? If we are going to 
        # copy data from the clean one, we need it to be unheadered,
        # but we also want to keep it unchanged.
        assert filesize == pure_rom_size, "Rom is headered!"
        # if filesize != pure_rom_size:
            # print("This is a headered rom, lets cut it off")
            # self.decapitate_rom(new_name)
            # checksum = _checksum(new_name)

        self.clean_rom = open(clean_name, "r+b")
        
        # Mod the rom if necessary
        if checksum == pure_rom_sum:
            print("Looks like a valid pure rom, we'll mod it first")
            self.new_rom = open(new_name, "r+b")
            self.mod_rom()
        # Load it if it already has the right mods
        # TODO: do we want this?
        elif checksum == modded_rom_sum:
            print("This is already modded, we can just load it")
            self.new_rom = open(new_name, "r+b")
        else: #TODO: restrict once we know what the checksums are supposed to be.
            print("Something is wrong with this rom")
            self.new_rom = open(new_name, "r+b")

    def mod_rom(self):
        """ *eventually* will modify a pure rom to have the mods we need """
        print("currently a stub")

    def decapitate_rom(self, filename):
        """removes the header from the rom """
        tmpname = filename + ".tmp"
        with open(filename, 'rb') as src:
            with open(tmpname, 'wb') as dest:
                src.read(512)
                dest.write(src.read())
        remove(filename)
        rename(tmpname, filename)

    def save_rom(self):
        """ Saves all changes to the rom, for now that just closes it"""
        self.clean_rom.close()
        self.new_rom.close()
        self.clean_rom = None
        self.new_rom = None

    def write_to_new(self, offset, data):
        """Write data to offset in the new rom"""
        if (isinstance(offset, Address)):
            offset = offset.as_PC()
        self.new_rom.seek(offset)
        self.new_rom.write(data)

    def read_from_new(self, offset, n_bytes):
        """Read n bytes from the new rom at offset"""
        if (isinstance(offset, Address)):
            offset = offset.as_PC()
        self.new_rom.seek(offset)
        r = self.new_rom.read(n_bytes)
        return r

    def read_from_clean(self, offset, n_bytes):
        """Read n bytes from the clean rom at offset"""
        if (isinstance(offset, Address)):
            offset = offset.as_PC()
        self.clean_rom.seek(offset)
        r = self.clean_rom.read(n_bytes)
        return r

    def smart_place_map(self, am, area):
        """ uses the lookup dictionary in areamap.py to translate
            a string area name into the addresses for placeMap()"""
        t = areamap.areamap_locs[area]
        self.place_map(am, t[1], t[0])

    def place_map(self, am, mapaddr, hiddenaddr):
        """When passed an areamap object, and the addresses to put the data in
           writes the relevant data to the rom. maybe one day an aditional
           "smart" version that knows these locations ahead of time will exist
        """
        mapdata = am.map_to_bytes()
        hiddendata = am.hidden_to_bytes()
        self.write_to_new(mapaddr, mapdata)
        self.write_to_new(hiddenaddr, hiddendata)

    def place_cmap(self, cmap_ts, mapaddr, hiddenaddr):
        """Uses the output from map_viz.cmap_to_tuples to create an amap then place it"""
        amap = areamap.tuples_to_amap(cmap_ts)
        mapdata = amap.map_to_bytes()
        #hiddendata = amap.hiddenToBytes()
        self.write_to_new(mapaddr, mapdata)
        #self.write_to_new(hiddenaddr, hiddendata)

