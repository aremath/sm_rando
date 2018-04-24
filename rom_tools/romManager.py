import level
import subprocess
import areamap
from address import Address
from shutil import copy2 as fileCopy
from hashlib import md5
from os import stat, remove, rename
import byte_ops

def _assertValid(addr):
    return byte_ops.assert_valid_SNES(addr)

def _PCtoSNES(addr):
    return byte_ops.PC_to_SNES(addr)


def _SNEStoPC(addr):
    return byte_ops.SNES_to_PC(addr)

def _intSplit(n):
    return byte_ops.int_split(n)

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

    def placeHeader(self, header):
        #TODO place headers for real
        #TODO lots of keeping track of headers information
        #TODO everything?
        print("Not Yet Implimented")

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


    def placeLevels(self, levelList):
        """ Take a list of Level objects, insert all of these into the ROM """

        ### Create lists of all the compressed level data, and the headers
        temp = list(zip(*[(x.data.getCompressed(), x.header) for x in levelList]))
        data = temp[0]
        headers = temp[1]


        for i in range(len(data)):
            ### Desired order:
                # Place Door Data (in bank 83)
                    # so we can place the door pointers in level header
                # place level data in bank (wherever)
                    # so we can place the data pointer in the header
                # Place level header in bank 8F



            ## Run through the list, placing data
            addr = self.placeBlock(data[i])
            convert = _intSplit(_assertValid(_PCtoSNES(addr)))
            ## and setting headers pointers approprietly
            headers[i].setDataPointer(convert)

        ## TODO Place the headers some day

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
