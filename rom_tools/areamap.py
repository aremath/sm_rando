# maptiles length 0x1000 bytes
# each 2 bytes is one "tile" for what that means
#

defaultMapSize = 0x800
defaultHiddenSize = 0x100

class MapTile(object):
	""" a single tile in an area map. representable as two bytes. contains logic
		to turn a set of easy to set parameters into the raw bytes"""
	def __init__(self):
		self.__default()

	def __default(self):
		self.vflip = False
		self.hflip = False
		self.color = 0
		self.tile = 0x1F
		self.hidden = True


	def __firstByte(self):
		return bytes([self.tile])


	def __secondByte(self):
		i = (0x04) * self.color
		if self.vflip:
			i += 0x80
		if self.hflip:
			i += 0x40
		return bytes([i])

	def toBytes(self):
		return self.__firstByte() + self.__secondByte()

	def isHidden(self):
		return not self.hidden

class AreaMap(object):
	""" a set of map tiles is an area map, can generate the whole map data
		including the midden bitmap"""
	def __init__(self):
		self.tileList = [MapTile()] * defaultMapSize

	def __rightSize(self):
		if (len(self.tileList) == defaultMapSize):
			return True
		else:
			return False

	def __isRightSize(self):
		if not self.__rightSize():
			print("Something is wrong")

	def mapToBytes(self):
		self.__isRightSize()
		x = bytes()
		for tile in self.tileList:
			x += tile.toBytes()
		return x

	def hiddenToBytes(self):
		l = []
		t = 0
		self.__isRightSize()
		for i in range(len(self.tileList)):
			if i > 0 and ((i % 8) == 0):
				l.append(t)
				t = 0
			t *= 2
			t += self.tileList[i].hidden
		l.append(t)
		return bytes(l)
