# maptiles length 0x1000 bytes
# each 2 bytes is one "tile" for what that means
# 

defaultMapSize = 0x800

class MapTile(object):
	"""docstring for MapTile"""
	def __init__(self):
		self.vflip = False
		self.hflip = False
		self.color = 0
		self.tile = 0
	def __firstByte(self):
		return bytes([0])
	def __secondByte(self):
		return bytes([0])
	def toBytes(self):
		return self.__firstByte() + self.__secondByte()


class Map(object):
	"""docstring for Map"""
	def __init__(self):
		self.tileList = [MapTile()] * defaultMapSize

	def __rightSize(self):
		if (len(self.tileList) == defaultMapSize):
			return True
		else:
			return False

	def toBytes(self):
		if not self.__rightSize():
			print("Something is wrong")
		x = bytes()
		for tile in self.tileList:
			x += tile.toBytes()
		return x
		