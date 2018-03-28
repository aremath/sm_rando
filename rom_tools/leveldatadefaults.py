air = [0xFF, 0x00]
block = [0x07, 0x81]

rowlen = 0x10 # or 0x20 cause it's by two? whatever
numrows = 0x10

cap = block*rowlen
middle = block + air*(rowlen - 2) + block

onebox = cap + middle*(numrows - 2) + cap


def buildBoxRoom(x, y):
	ourlen = rowlen * x
	ournum  = numrows * y
	size = (ourlen * ournum)*2
	cap = block * ourlen
	middle = block + air*(ourlen - 2) + block
	ourbox = cap + middle*(ournum - 2) + cap
	if (not (size == len(ourbox))):
		print("BUILDBOXROOM broke")
		print("Expected length of " + str(size) +" but got " + str(len(ourbox)))
	else:
		return ourbox
