from functools import reduce
import os 
from subprocess import Popen, PIPE, STDOUT
import leveldatadefaults as datadefs

def __deleteIfExists(self, filename):
	try:
		os.remove(filename)
	except OSError:
		pass


class Level(object):
	"""docstring for Level"""
	def __init__(self, size=(1,1), doors=1):

		### Level Header Information 
		self.header = RoomHeader(doors=doors)
		self.header.setSize(size)
		### Level Data Information
		self.data = LevelData(size)
		self.levelpointer = [0x00,0x00,0x00]
		self.doors = [Door()] * doors
		self.doorPointers = [[0x00,0x00] * doors]

	def newDoor(self):
		self.doors.append(Door())





	def setDataPointer(self, addr):
		self.levelpointer = addr
		self.header.setDataPointer(addr)



class RoomHeader(object):




	defaultIntro = [
	0,		# Room Index
	0,		# Room Area
	0,		# X on Map
	0,		# Y on Map
	1,		# Width of Room
	1,		# Height of Room
	0x90,	# Up scroller Value
	0xA0,	# Down Scroller Value
	0,		# Special Graphics?
	0,0]	# Door Out Pointer TODO what?

	defaultStandardPointers = [
	0,0,	# STD 1 Pointer
	0,0,0,	# Level Data Pointer
	0,		# TileSet
	0,		# Song Set
	0,		# Play Index
	0,0, 	# FX pointer
	0,0,	# Enemy Set Pointer
	0,0,	# Enemy GFX Pointer
	0,0, 	# BG x/y scrolling
	0,0, 	# Room Scolls Pointer
	0,0, 	# UNUSED 
	0,0, 	# Main ASM pointer
	0,0, 	# PLM set pointer
	0,0, 	# Background Pointer
	0,0] 	# Setup ASM Pointer





	def __init__(self, doors=1, events=0):
		#### Layout ####
		# 11 Standard bytes
		# 5 extra bytes per Event 
		# 28 standard bytes
		# 26 extra bytes per event
		# 2 bytes per door
		self.intro = list(self.defaultIntro)
		self.eventIntro = [[0x00]*(events * 5)]
		self.standardPointers = list(self.defaultStandardPointers)
		self.eventPointers = [[0x00] * (events * 26)]
		self.doorPointers = [[0x00,0x00]*doors]

	def setNumDoors(self,n):
		self.doorPointers = [[0x00,0x00]*n]

	def setSize(self,size):
		x=size[0]
		y=size[1]
		self.intro[4] = x
		self.intro[5] = y


	def dataToHex(self):
		i = bytes(self.intro)
		ei = reduce((lambda x, y: x+y),map(bytes,self.eventIntro))
		sp = bytes(self.standardPointers)
		ep = reduce((lambda x, y: x+y),map(bytes,self.eventPointers))
		dp = reduce((lambda x, y: x+y),map(bytes,self.doorPointers))
		return i + ei + sp + ep + dp

	def setDataPointer(self,addr):
		if len(addr) != 3:
			raise IndexError
		for i in range(len(addr)):
			self.standardPointers[i+2] = addr[i]
		return False

class LevelData(object):

	
	def __init__(self, size=(1,1)):
		### Level Data Information
		self.size = size
		n = size[0]*size[1]
		self.levelstart = [0x00,n]
		self.tiledata = [0x00]*0x200*n
		self.background = []
		self.prgmdata = [0x00]*0x100*n

	def makeBox(self):
		x = self.size[0]
		y = self.size[1]
		newdat = datadefs.buildBoxRoom(x,y)
		if (not (len(newdat) == len(self.tiledata))):
			print("MAKE BOX IS BROKEN SOMEHOW")
		else:
			self.tiledata = newdat


	def dataToHex(self):
		return reduce((lambda x, y: x+y),map(bytes,[self.levelstart,self.tiledata, self.background, self.prgmdata]))

	def getCompressed(self):
		#TODO Find way around killing process
		#why do communicate and stdin.write no work?
		hx = self.dataToHex()
		file1 = "temp"
		file2 = "temp.dec"
		with open(file1, "wb") as f:
			f.write(hx)
		args = "recomp.exe "+file1+" "+file2+" 0 4 0"
		p = Popen(args,stdin = PIPE, stdout = PIPE, stderr = STDOUT)
		i = 0
		try:
			p.wait(2)
		except:
			p.kill()
		##subprocess.call(args)
		comp = []
		with open(file2,"rb") as f:
			byte = f.read(1)
			while byte != bytes():
				comp.append(byte)
				byte = f.read(1)
		return bytes(map(lambda x: int.from_bytes(x,'little'),comp))

	def __genericSafeGet(self, data, leng):
		if len(data) != leng:
			raise IndexError  
		elif (type(data) is not list) or (type(data[0]) is not int):
			raise TypeError 
		else:
			return data


	def setTileData(self, data):
		self.tiledata = self.__genericSafeGet(data, len(self.tiledata))


	def setProgramData(self, data):
		self.prgmdata = self.__genericSafeGet(data, len(self.prgmdata))
	

class Door(object):

	default = [
	0,0,		# Room ID, Destination (HOW?)
	0,			# Bitflag (00 for default, 40 for new area, 80 for elev same area, c0 for elev to new area)
	0,			# Direction (0-r) (1-l) (2-d) (3-u) (same +4 for auto-close)
	0,			# Door top x
	0,			# Door top y
	0,			# screen x (which screen is it on?)
	0,			# screen y
	0,0,		# distance from spawn? (LR 80 00) (up 01 c0) (down 01 40)
	0,0]		# door ASM pointer 

	"""docstring for Door"""
	def __init__(self):
		self.data = [0x00]*12


	def dataToHex(self):
		return bytes(self.data)

		
