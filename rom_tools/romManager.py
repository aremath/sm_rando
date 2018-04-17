import level
import subprocess
import areamap
from shutil import copy2 as fileCopy
from hashlib import md5

def _validSNES(addr):
	"""Checks a givven snes lorom address to see if it is a valid adress"""
	if (addr < 0) or (addr >0x1000000):
		return False
	else:
		m = ((addr & 0xFF0000) >> 16) % 2 == 0
		b = addr & 0x8000 != 0
		return m != b

def _assertValid(addr):
	if not _validSNES(addr):
		raise IndexError
	else:
		return addr

def _PCtoSNES(addr):
	""" Converts from a PC rom adress to a snes lorom one"""
	a = ((addr << 1) & 0xFF0000) + 0x800000
	b = addr & 0xFFFF
	return a|b


def _SNEStoPC(addr):
	"""Converts LORAM addresses to PC Addresses."""
	return ((addr & 0x7f0000) >> 1) | (addr & 0x7FFF)

def _intSplit(n):
	""" Splits and Endians pointers for "ROM MODE" """
	l = []
	a=n
	while a > 0:
		l = l + [a&0xFF]
		a = a >> 8
	return l

def _backupFile(filename):
	""" Just tries to bakup the rom for easy re-use """
	try:
		fileCopy(filename, filename + ".bak")
	except:
		print("FILE DOESN'T EXIST")





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
		self.rom = open(filename, "r+b")
		if self.__checksum():
			print("WORKED")

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
		self.rom.seek(offset)
		self.rom.write(data)

	def readFromRom(self, offset, numbytes):
		"""read a number of bytes from a certain offset"""
		self.rom.seek(offset)
		r = self.rom.read(numbytes)
		return r

	def __checksum(self):
		"""check if this file is a 'pure' copy of the rom"""
		# TODO takes checksum wrong somehow?
		# TODO actually compare with correct answer
		self.rom.seek(0)
		check = md5(self.rom.read()).hexdigest()
		print(check)
		return True #TODO not this

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

	def placeMap(self, areamap, mapaddr, hiddenaddr):
		"""When passed an areamap object, and the addresses to put the data in
		   writes the relevant data to the rom. maybe one day an aditional
		   "smart" version that knows these locations ahead of time will exist
		"""
		mapdata = areamap.mapToBytes()
		hiddendata = areamap.hiddenToBytes()
		self.writeToRom(mapaddr, mapdata)
		self.writeToRom(hiddenaddr, hiddendata)
