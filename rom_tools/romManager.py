import level
import subprocess
import areamap
from memory import Bank
from address import Address
from shutil import copy2 as fileCopy
from hashlib import md5
from os import stat, remove, rename
import byte_ops

def _backupFile(filename):
    """ Just tries to bakup the rom for easy re-use """
    try:
        fileCopy(filename, filename + ".bak")
    except:
        print("FILE DOESN'T EXIST")

def _takeChecksum(filename):
    """ md5sums a file """
    with open(filename, 'rb') as file:
        m = md5()
        while True:
            data = file.read(4048)
            if not data:
                break
            m.update(data)
    return m.hexdigest()

def _fileLength(filename):
    statinfo = stat(filename)
    return statinfo.st_size


class RomManager(object):
    """The Rom Manager handles the actual byte facing aspects of the rom editing
       Can be used to both read and write to the rom, also contains meta data
       to make inserting rooms and room headers easier.
       Also *eventually* will be able to detect if your rom is `pure` and apply
       some necessary patches auto-magically"""

    def __init__(self,romname = None):
        #TODO all these values are rough estimate placeholders, replace eventually.
        self.freeBlock = 0x220000
        self.lastBlock = 0x277FFF
        self.freeHeader = 0x78000
        self.lastHeader = 0x7FFFF

        if romname != None:
            self.loadRom(romname)

    def loadRom(self, filename):
        """actually loads the rom by filename, also saves a backup of the rom
           before any changes have been made"""
        _backupFile(filename)


        pureRomSum = '21f3e98df4780ee1c667b84e57d88675'
        moddedRomSum = 'idk'
        pureRomSize = 3145728

        checksum = _takeChecksum(filename)
        filesize = _fileLength(filename)
        if not filesize == pureRomSize:
            print("This is a headered rom, lets cut it off")
            self.decapitateRom(filename)
            checksum = _takeChecksum(filename)


        if checksum == pureRomSum:
            print("Looks like a valid pure rom, we'll mod it first")
            self.rom = open(filename, "r+b")
            self.modRom()
        elif checksum == moddedRomSum:
            print("This is already modded, we can just load it")
            self.rom = open(filename, "r+b")
        else: #TODO: restrict once we know what the checksums are supposed to be.
            print("Something is wrong with this rom")
            self.rom = open(filename, "r+b")

    def modRom(self):
        """ *eventually* will modify a pure rom to have the mods we need """
        print("currently a stub")

    def decapitateRom(self, filename):
        """removes the header from the rom """
        tmpname = filename + ".tmp"
        with open(filename, 'rb') as src:
            with open(tmpname, 'wb') as dest:
                src.read(512)
                dest.write(src.read())
        remove(filename)
        rename(tmpname, filename)

    def saveRom(self):
        """ Saves all changes to the rom, for now that just closes it"""
        self.rom.close()
        self.rom = None


    def placeBlock(self, block):
        """ Given a block of compressed level data, places it in the next spot, returns PC address"""
        length = len(block)
        offset = self.freeBlock
        self.freeBlock += length
        print("Placing block of size: 0x%x at address: 0x%x\nnew freeBlock: 0x%x" % (length, offset, self.freeBlock))
        self.writeToRom(offset, block)
        print("Space left in levelData Banks: 0x%x" % (self.lastBlock - self.freeBlock))
        return offset

    def writeToRom(self, offset, data):
        """ With some bytes and an offset, we can write that to the rom"""
        if (isinstance(offset, Address)):
            offset = offset.as_PC()
        self.rom.seek(offset)
        self.rom.write(data)

    def readFromRom(self, offset, numbytes):
        """read a number of bytes from a certain offset"""
        if (isinstance(offset, Address)):
            offset = offset.as_PC()
        self.rom.seek(offset)
        r = self.rom.read(numbytes)
        return r


    def _init_banks(self):
        print("stub")
        self.level_data_bank = Bank()
        self.doors_bank = Bank()
        self.headers_bank = Bank()
        return

    def placeLevels(self, levelList):
        """ Take a list of Level objects, insert all of these into the ROM """
        ## compress all the data at the start
        print("Compressing Data")
        for level in levelList:
            level.compress_data()
        print("Compressed all the data!.... finally")

        ## place level data and door data, updating headers along the way
        for level in levelList:
            level_addr = self.place_level_data(level.data_compressed)
            level.set_data_addr(level_addr)
            door_addrs = list(map(self.place_door_data, level.doors))
            level.set_door_addrs(door_addrs)

        ## place the headers in places (updating the door objects along the way)
        for level in levelLists:
            addr = self.place_header(level.header)
            level.set_header_addr(addr)

        ## update the doors
        for level in levelList:
            self.update_doors(level)

        # order of oporations:
        # 	(
        # 		place level data
        # 		place door data
        #       *eventually plm data*
        # 	)
        # 	update header
        # 	place header + door pointers
        # 	- do this for every room
        # 	update door data

    def place_level_data(self, data):
        size = len(data)
        addr = self.level_data_bank.get_place(size)
        assert(isinstance(addr, Address))
        self.writeToRom(addr.as_PC(), data)
        return addr

    def place_door_data(self, door):
        assert(isinstance(door, level.Door))
        data = door.dataToHex()
        size = len(data)
        addr = self.doors_bank.get_place(size)
        assert(isinstance(addr, Address))
        self.writeToRom(addr.as_PC(), data)
        return addr

    def place_header(self, header):
        assert(isinstance(header, level.Header))
        data = header.dataToHex()
        size = len(data)
        addr = self.headers_bank.get_place(size)
        assert(isinstance(addr, Address))
        self.writeToRom(addr.as_PC(), data)
        return addr

    def update_doors(self, level):
        assert(isinstance(level, Level))
        for addr, door in zip(level.door_addrs, level.doors):
            data = door.dataToHex()
            dest = addr.as_PC()
            self.writeToRom(dest, data)


    def smartPlaceMap(self, am, area):
        """ uses the lookup dictionary in areamap.py to translate
            a string area name into the addresses for placeMap()"""
        t = areamap.areamapLocs[area]
        self.placeMap(am, t[1], t[0])

    def placeMap(self, am, mapaddr, hiddenaddr):
        """When passed an areamap object, and the addresses to put the data in
           writes the relevant data to the rom. maybe one day an aditional
           "smart" version that knows these locations ahead of time will exist
        """
        mapdata = am.mapToBytes()
        hiddendata = am.hiddenToBytes()
        self.writeToRom(mapaddr, mapdata)
        self.writeToRom(hiddenaddr, hiddendata)

    def placeCmap(self, cmap_ts, mapaddr, hiddenaddr):
        """Uses the output from map_viz.cmap_to_tuples to create an amap then place it"""
        amap = areamap.tuples_to_amap(cmap_ts)
        mapdata = amap.mapToBytes()
        #hiddendata = amap.hiddenToBytes()
        self.writeToRom(mapaddr, mapdata)
        #self.writeToRom(hiddenaddr, hiddendata)

#TODO: consistent naming schemes

# r=RomManager()
# path="rom_files/pure.smc"
# r.loadRom(path)
# am = areamap.AreaMap()
