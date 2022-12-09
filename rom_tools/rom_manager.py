from shutil import copy2 as copy_file
from hashlib import md5
from os import stat, remove, rename
from collections import defaultdict
from pathlib import Path

from . import byte_ops
from . import areamap
from .memory import *
from .address import Address
#TODO: register the methods as part of importing compress
from .compress import decompress
from .compress import compress
from . import rom_data_structures

# Addresses of the maps for the different regions
# https://patrickjohnston.org/bank/82#f9717
# https://patrickjohnston.org/bank/B5
region_map_locs = { # hidden |  tiles
    "Wrecked_Ship" : (Address(0x11a27), Address(0x1ab000)),
    "Maridia"      : (Address(0x11b27), Address(0x1ac000)),
    "Crateria"     : (Address(0x11727), Address(0x1a9000)),
    "Norfair"      : (Address(0x11927), Address(0x1aa000)),
    "Brinstar"     : (Address(0x11827), Address(0x1a8000)),
    "Tourian"      : (Address(0x11c27), Address(0x1ad000))
}

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

    def load_rom(self, clean_name, new_name, mod=True):
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
        self.new_rom = open(new_name, "r+b")
        #TODO: Restrict based on checksum
        if mod:
            self.mod_rom()

    def mod_rom(self):
        """
        Mod the ROM with various patches (see comments)
        """
        # Skip Ceres
        self.write_to_new(Address(0x16ebb), b"\x05")
        # Make sand easier to jump out of without gravity
        self.write_to_new(Address(0x2348c), b"\x00")
        self.write_to_new(Address(0x234bd), b"\x00")
        # Remove gravity suit heat protection
        self.write_to_new(Address(0x6e37d), b"\x01")
        self.write_to_new(Address(0x869dd), b"\x01")
        # Suit animation skip #TODO
        self.write_to_new(Address(0x20717), b"\xea\xea\xea\xea")
        # Fix heat damage speed echoes bug #TODO: verify
        self.write_to_new(Address(0x8b629), b"\x01")
        # Disable GT Code #TODO: verify
        self.write_to_new(Address(0x15491c), b"\x80")
        # Fix chozo/hidden morph item actually giving spring ball
        self.write_to_new(Address(0x268ce), b"\x04")
        self.write_to_new(Address(0x26e02), b"\x04")
        # Fix screw attack selection
        self.write_to_new(Address(0x134c5), b"\x0c")
        # Apply other IPSs #TODO: make sure this works!
        patches_path = Path(__file__).parent.parent / "patches"
        self.apply_ips(patches_path / "g4_skip.ips")
        self.apply_ips(patches_path / "max_ammo_display.ips")
        self.apply_ips(patches_path / "wake_zebes.ips")
        self.apply_ips(patches_path / "mother_brain_no_drain.ips")
        # Applied based on settings
        #self.apply_ips(patches_path / "teleport.ips")
        # Fix sand rooms so that you can't get stuck
        #TODO: find out what is wrong with this
        #self.apply_ips(patches_path / "no_sand_bs.ips")

    def set_escape_timer(self, time):
        # Change escape timer
        # First, convert to minutes, seconds:
        minutes = time // 60
        seconds = time % 60
        # Get the times as bytes
        minute_bytes = minutes.to_bytes(1, byteorder='little')
        second_bytes = seconds.to_bytes(1, byteorder='little')
        # Write them
        self.write_to_new(Address(0x0001e21), second_bytes)
        self.write_to_new(Address(0x0001e22), minute_bytes)

    def decapitate_rom(self, filename):
        """ Removes the header from the rom """
        tmpname = filename + ".tmp"
        with open(filename, 'rb') as src:
            with open(tmpname, 'wb') as dest:
                src.read(512)
                dest.write(src.read())
        remove(filename)
        rename(tmpname, filename)

    def save_and_close(self):
        """ Saves all changes to the rom, for now that just closes it"""
        self.clean_rom.close()
        self.new_rom.close()
        self.clean_rom = None
        self.new_rom = None

    def write_to_new(self, offset, data):
        """Write data to offset in the new rom"""
        self.new_rom.seek(offset.as_pc)
        self.new_rom.write(data)

    def read_from_new(self, offset, n_bytes):
        """Read n bytes from the new rom at offset"""
        self.new_rom.seek(offset.as_pc)
        r = self.new_rom.read(n_bytes)
        return r

    def read_from_clean(self, offset, n_bytes):
        """Read n bytes from the clean rom at offset"""
        self.clean_rom.seek(offset.as_pc)
        r = self.clean_rom.read(n_bytes)
        return r

    def read_array(self, offset, array_width, array_height, element_size, rom="clean"):
        if rom == "clean":
            read = self.read_from_clean
        elif rom == "new":
            read = self.read_from_new
        else:
            assert False, "Bad rom option"
        #TODO: is dict really the best option?
        array = defaultdict(dict)
        for x in range(array_width):
            for y in range(array_height):
                array_offset = (y * array_width + x) * element_size
                array[x][y] = read(offset + array_offset, element_size)
        return array

    def read_list(self, offset, element_size, list_length, rom="clean", check_length=True, compressed=True):
        if rom == "clean":
            read = self.read_from_clean
        elif rom == "new":
            read = self.read_from_new
        else:
            assert False, "Bad rom option"
        total_size = list_length * element_size
        # The compressed data should be shorter than the total size of the uncompressed list
        compressed_data = read(offset, total_size)
        if compressed:
            data = decompress.decompress(compressed_data)
        else:
            data = compressed_data
        # If you aren't certain of the true length of the list, set check_length = False
        if check_length:
            assert len(data) == total_size, (len(data), total_size)
        # Either way, the total amount of data has to be a multiple of the element size
        else:
            assert len(data) % element_size == 0
        l = []
        for i in range(0, total_size, element_size):
            l.append(data[i:i+element_size])
        return l

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
        #TODO: why does hidden data corrupt the map?
        #hiddendata = amap.hiddenToBytes()
        self.write_to_new(mapaddr, mapdata)
        #self.write_to_new(hiddenaddr, hiddendata)

    # Thanks to the main SM item rando for this
    def apply_ips(self, ips_file, offset=5):
        ips = open(ips_file, "rb")
        while True:
            ips.seek(offset)
            ips_address_b = ips.read(3)
            if ips_address_b == b"\x45\x4f\x46":
                break
            ips.seek(offset + 3)
            ips_length_b = ips.read(2)
            ips_address = Address(int.from_bytes(ips_address_b, byteorder='big'))
            ips_length = int.from_bytes(ips_length_b, byteorder='big')
            # Update offset past the end of the bytes we just read
            offset += 5
            
            # 0 is the code for - get a new length then write one byte that many times
            if ips_length == 0:
                ips.seek(offset)
                new_length_b = ips.read(2)
                new_length = int.from_bytes(new_length_b, byteorder='big')
                ips.seek(offset + 2)
                data = ips.read(1) * new_length
                self.write_to_new(ips_address, data)
                offset += 3
            # Get length bytes at offset and write them
            else:
                ips.seek(offset)
                data = ips.read(ips_length)
                self.write_to_new(ips_address, data)
                offset += ips_length
        ips.close()

    def apply_patches(self, patches):
        for address, data in patches:
            self.write_to_new(address, data)

    def save_table_entries(self, address):
        save_station_size = Address(14)
        addrs = []
        while self.read_from_clean(address, 2) != b"\x00\x00":
            addrs.append(address)
            address += save_station_size
        return addrs

    def parse(self):
        # Vanilla Savestations
        crateria_save_table = Address(0x0044c5, mode="pc")
        crateria_savestations = self.save_table_entries(crateria_save_table)
        assert len(crateria_savestations) == 2
        brinstar_save_table = Address(0x0045cf, mode="pc")
        brinstar_savestations = self.save_table_entries(brinstar_save_table)
        assert len(brinstar_savestations) == 5
        norfair_save_table = Address(0x0046d9, mode="pc")
        norfair_savestations = self.save_table_entries(norfair_save_table)
        assert len(norfair_savestations) == 6
        wrecked_ship_save_table = Address(0x00481b, mode="pc")
        wrecked_ship_savestations = self.save_table_entries(wrecked_ship_save_table)
        assert len(wrecked_ship_savestations) == 1
        maridia_save_table = Address(0x004917, mode="pc")
        maridia_savestations = self.save_table_entries(maridia_save_table)
        assert len(maridia_savestations) == 4
        tourian_save_table = Address(0x004a2f, mode="pc")
        tourian_savestations = self.save_table_entries(tourian_save_table)
        assert len(tourian_savestations) == 2
        #TODO: what about Ceres?
        all_saves = crateria_savestations + brinstar_savestations + norfair_savestations + \
                wrecked_ship_savestations + maridia_savestations + tourian_savestations
        obj_names = rom_data_structures.parse_from_savestations(all_saves, self)
        # Register the objects with the memory model so that we don't allocate new levels
        # on top of existing ones
        for obj in obj_names.values():
            if type(obj.old_address) is Address:
                self.memory.mark_filled(obj.old_address, obj.old_size)
        return obj_names

    def clear_memory(self):
        self.memory = Memory(self)
        self.memory.setup()

    def compile(self, obj_names):
        all_saves = [obj for obj in obj_names.values() if isinstance(obj, rom_data_structures.SaveStation)]
        print(f"Saves: {all_saves}")
        rom_data_structures.compile_from_savestations(all_saves, obj_names, self)

