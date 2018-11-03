from functools import reduce
import os
from subprocess import Popen, PIPE, STDOUT
from . import leveldatadefaults as datadefs
from . import byte_ops
from .address import Address
from .compress import compress

def __delete_if_exists(self, filename):
    try:
        os.remove(filename)
    except OSError:
        pass

class Room(object):

    def __init__(self, size=(1,1), doors=1):

        ### Level Header Information
        self.header = RoomHeader(doors=doors)
        self.header.setSize(size)
        self.header_addr = None
        ### Level Data Information
        self.data = LevelData(size)
        self.data_addr = None
        self.doors = [Door()] * doors
        self.door_addrs = [Address()] * doors

    def set_header_addr(self,addr):
        if not (isinstance(addr, Address)):
            print("Please pass me an Address Object, not a number")
        self.header_addr = addr
        for door in self.doors:
            door.room_id = addr.as_room_id()

    def set_data_addr(self, addr):
        self.levelpointer = addr
        self.header.set_data_addr(addr)

    def compress_data(self):
        self.data_compressed = self.data.getCompressed()

    def set_door_addrs(self, addrs):
        assert(len(addrs) == len(self.door_addrs))
        self.door_addrs = addrs
        self.header.set_door_pointers(self.door_addrs)


def convert_event(event_value, event_arg):
    events = [(0xe5e6, 0), (0xe5eb, 2), (0xe5ff, 0), (0xe612, 1), (0xe629, 1),
            (0xe640, 0), (0xe652, 0), (0xe669, 0), (0xe678, 0)]
    arg_len = [v[1] for v in events if v[0] == event_value]
    assert len(arg_len) == 1, "Invalid event type: " + str(event_value)
    ea = event_arg.to_bytes(arg_len[0], byteorder='little')
    ev = event_value.to_bytes(2, byteorder='little')
    ehead = ea + ev
    return ehead

def get_future_ptr(ptr_arg, name, head_ptr):
    # I do not like using isinstance, but it is useful here to identify whether we are using a
    # pre-allocated pointer, or something that's room-specific (or a nullptr)
    if ptr_arg is None:
        return None
    # Some of the room data are pre-allocated. I don't want to have a "snes-assembly"
    # object for each room, especially when multiple rooms are running the same assembly code.
    # It makes sense to have defaults which are shared between rooms so that they aren't allocated
    # multiple times, or so that I don't have to read them into a special data structure before
    # re-writing the exact same bytes. These defaults are stored in the env under their name.
    # Also useful for things like default scrolls which do not need to be allocated.
    elif isinstance(ptr_arg, str):
        return FutureAddress(ptr_arg)
    # An index into this rooms name-list. For leveldata, each room has a list of leveldata
    # which is allocated as part of allocating the room. Each room header is passed a leveldata
    # to use, which is an index into that list.
    elif isinstance(ptr_arg, int):
        return FutureAddress(head_ptr + name + "_{}".format(ptr_arg))
    else:
        assert False, "Bad type for futureaddr"

class RoomState(object):
    """A roomstate is a configuration for a room. Corresponds to 'event' in the SMILE guide.
    Every room needs at least one default roomstate, but various events can trigger more. """
    
    def __init__(self, room_id, event_id, event_value=0xe5e6, event_arg=None, level_data, tileset, song,
            fx, enemies, enemy_set, background_scroll_xy, scrolls, main_asm, plms, background, setup_asm):

        # Data members that are read in as bytes
        if self.event_value = 0xe5e6:
            self.default_event=True
        else:
            self.default_event=False
        self.event_head = convert_event(event_value, event_arg)
        self.tileset = tileset.to_bytes(1, byteorder='little')
        self.song = song.to_bytes(2, byteorder='little')
        self.background_scrolls = background_scroll_xy[0].to_bytes(1, byteorder='little')
        self.background_scrolls += background_scroll_xy[1].to_bytes(1, byteorder='little')
        self.background = background.to_bytes(2, byteorder='little')
       
        # Data members that will be allocated then become pointers
        sym_ptr = "room_{}_".format(room_id)
        self.sym_ptr = sym_ptr
        self.level_data_ptr = get_future_ptr(level_data, "leveldata", sym_ptr)
        self.fx_ptr = get_future_ptr(fx, "fx", sym_ptr)
        # A note on enemies vs. enemy set: enemies refers to the actual enemies that
        # are present in the room. Enemy set refers to the types of enemies that can be
        # present. Confusingly, these correspond respectively to the "enemy set" and
        # "enemy gfx" pointers that are referred to in the SMILE guide. My naming scheme
        # corresponds to the metconst wiki page, and I think these names are better anyway.
        self.enemies_ptr = get_future_ptr(enemies, "enemies", sym_ptr) 
        self.enemy_set_ptr = get_future_ptr(enemy_set, "enemy_set", sym_ptr) 
        self.scrolls_ptr = get_future_ptr(scrolls, "scrolls", sym_ptr) 
        self.main_asm_ptr = get_future_ptr(main_asm, "main_asm", sym_ptr) 
        self.plms_ptr = get_future_ptr(plms, "plms", sym_ptr)
        self.setup_asm_ptr = get_future_ptr(setup_asm, "setup_asm", sym_ptr)

    def to_bytes(self, event_id):
        futures = []
        # This is a future pointer to where the event's state will be within the room header
        state_ptr = FutureAddress(name=self.sym_ptr + "state_{}".format(event_id))
        if self.default_event = True:
            head = self.event_head
        # The extra two bytes will be used to store a pointer to the rest of the event data
        # In this case the FutureAddrWrite will be generated when allocating the RoomHeader
        # because the RoomState has no information about where it will be put inside the
        # RoomHeader.
        else:
            head = self.event_head + b"\x00\x00"
        tail = b""
        tail += b"\x00\x00\x00"
        if self.level_data_ptr is not None:
            futures.append(FutureAddressWrite(self.level_data_ptr, state_ptr, 3)) # 3
        tail += self.tileset    # 4
        tail += self.song       # 6
        tail += b"\x00\x00"
        if self.fx_ptr is not None:
            futures.append(FutureAddressWrite(self.fx_ptr, state_ptr + 0x6, 2, bank=0x83)) # 8
        tail += b"\x00\x00"
        if self.enemies_ptr is not None:
            futures.append(FutureAddressWrite(self.enemies_ptr, state_ptr + 0x8, 2, bank=0xa1)) # a
        tail += b"\x00\x00"
        if self.enemy_set_ptr is not None:
            futures.append(FutureAddressWrite(self.enemy_set_ptr, state_ptr + 0xa, 2, bank=0xb4)) # c
        tail += background_scrolls # e
        tail += b"\x00\x00"
        if self.scroll_ptr is not None:
            futures.append(FutureAddressWrite(self.scroll_ptr, state_ptr + 0xe, 2, bank=0x8f)) # 10
        tail += b"\x00\x00" # 12 - special xray stuff - I'm not using it for now
        tail += b"\x00\x00"
        if self.main_asm_ptr is not None:
            futures.append(FutureAddressWrite(self.main_asm_ptr, state_ptr + 0x12, 2, bank=0x8f)) # 14
        tail += b"\x00\x00"
        if self.plms_ptr is not None:
            futures.append(FutureAddressWrite(self.plms_ptr, state_ptr + 0x14, 2, bank=0x8f)) # 16
        tail += b"\x00\x00"
        if self.setup_asm_ptr is not None:
            futures.append(FutureAddressWrite(self.setup_asm_ptr, state_ptr + 0x16, 2, bank=0x8f)) # 18
        assert len(tail) == 26
        return head, tail, futures

class RoomHeader(object):
    """Represents a room header."""

    def __init__(self, room_id, room_index, room_area, map_xy, room_size_xy, up_scroll=0x90, down_scroll=0xa0,
            special_graphics=0, room_states, levels, fxs, enemies, enemy_sets,
            scrolls, main_asms, plms, setup_asms, doors):
        
        # Data members that are read in as bytes
        self.room_index = room_index.to_bytes(1, byteorder='little')
        self.room_area = room_area.to_bytes(1, byteorder='little')
        self.map_x = map_xy[0].to_bytes(1, byteorder='little')
        self.map_y = map_xy[1].to_bytes(1, byteorder='little')
        self.room_size_x = room_size_xy[0].to_bytes(1, byteorder='little')
        self.room_size_y = room_size_xy[1].to_bytes(1, byteorder='little')
        self.up_scroll = up_scroll.to_bytes(1, byteorder='little')
        self.down_scroll = down_scroll.to_bytes(1, byteorder='little')
        self.special_graphics = special_graphics.to_bytes(1, byteorder='little')

        # Data members that will be allocated
        sym_ptr = "room_{}_".format(room_id)
        self.sym_ptr = sym_ptr
        self.header_ptr = FutureAddress(sym_ptr " _head")
        self.doors_ptr = FutureAddress(sym_ptr + "_doors")

    #TODO: can put this calculation directly in __init__ - at this point there should be
    # no need to know what the actual data members are (same with room_header)
    def head_bytes(self):
        head = b""
        futures = []
        head += self.room_index         # 1
        head += self.room_area          # 2
        head += self.map_x              # 3
        head += self.map_y              # 4
        head += self.room_size_x        # 5
        head += self.room_size_y        # 6
        head += self.up_scroll          # 7
        head += self.down_scroll        # 8
        head += self.special_graphics   # 9
        head += b"\x00\x00"             # 11
        # Write at the end of the header a future pointer to where the doors are placed
        futures.append(FutureAddressWrite(self.doors_ptr, self.header_ptr + 0x9, 2, bank=0x8f))
        assert len(head) == 11
        return head, futures

    def allocate(self, bank, env):
        # Allocate levels, fxs, enemies, enemy_sets, scrolls, main_asms, plms, setup_asms, doors
        # Generate to_bytes() using head_bytes, then room_states bytes, then FutureWrites for door ptrs
        # - during generation add state ptrs into the env
        # - during generation add doors ptr into the env
        # Allocate self with size of to_bytes

        pass

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

    def set_num_doors(self,n):
        self.door_pointers = [[0x00,0x00]*n]

    def set_size(self,size):
        x=size[0]
        y=size[1]
        self.intro[4] = x
        self.intro[5] = y

    def set_address(self, addr):
        if not (isinstance(addr, Address)):
            print("Pass me an address object please")
            assert(False)
        ln = len(self.dataToHex)
        door_offset = ln - (len(self.doorPointers))
        door_addr = addr.copy_increment(door_offset)
        doot_bytes = door_addr.as_room_id_endian()
        assert(len(door_bytes) == 2)
        self._set_door_out_bytes(door_bytes)

    def _set_door_out_bytes(self,bytes):
        index = 9
        self.intro[index + 0] = bytes[0]
        self.intro[index + 1] = bytes[1]

    def set_door_pointers(self, pointers):
        assert(len(self.doorPointers) == len(pointers))
        self.doorPointers = pointers

    def data_to_hex(self):
        i = bytes(self.intro)
        ei = reduce((lambda x, y: x+y),map(bytes,self.event_intro))
        sp = bytes(self.standard_pointers)
        ep = reduce((lambda x, y: x+y),map(bytes,self.event_pointers))
        dp = reduce((lambda x, y: x+y),map(bytes,self.door_pointers))
        return i + ei + sp + ep + dp

    def set_data_addr(self,addr):
        # TODO update for new addr object
        if len(addr) != 3:
            raise IndexError
        for i in range(len(addr)):
            self.standardPointers[i+2] = addr[i]
        return False

class LevelData(object):
    """ Contains all the level data (just a giant array of bytes) including
        the background data if need be """

    def __init__(self, size=(1,1)):
        ### Level Data Information
        self.size = size
        n = size[0]*size[1]
        self.levelstart = [0x00,n] # pretty sure levelstart should be the number of bytes in the uncompresssed tile data
        self.tiledata = [0x00]*0x200*n
        self.background = []
        self.prgmdata = [0x00]*0x100*n

    def makeBox(self):
        x = self.size[0]
        y = self.size[1]
        newdat = datadefs.buildBoxRoom(x,y)
        assert len(newdat) == len(self.tiledata), "MAKE BOX IS BROKEN SOMEHOW"
        self.tiledata = newdat
        
    def dataToHex(self):
        return reduce((lambda x, y: x+y),map(bytes,[self.levelstart,self.tiledata, self.background, self.prgmdata]))

    def getCompressed2(self):
        return compress.compress(self.dataToHex())

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
    """ Door object which *eventually* will contain all the data a door needs to
        be put on the rom."""

    default = [
    0,0,        # Room ID, Destination. an address bank $8F
    0,          # Bitflag (00 for default, 40 for new area, 80 for elev same area, c0 for elev to new area)
    0,          # Direction (0-r) (1-l) (2-d) (3-u) (same +4 for auto-close)
    0,          # Door top x (horizontal position of the closing blue door cap in the next room, counted in tiles.)
    0,          # Door top y (vertical position of the closing blue door cap in the next room, counted in tiles.)
    0,          # screen x counted from the very left in screens. [other room?]
    0,          # screen y counted from the very top in screens.
    0,0,        # distance from spawn? (LR 80 00) (up 01 c0) (down 01 40)
    0,0]        # door ASM pointer

    def __init__(self):
        self.newArea = False
        self.isElevator = False
        self.direction = 0 #(0-r) (1-l) (2-d) (3-u)
        self.autoClose = False
        self.room_id = 0xffff
        self.top_loc = (0,0)
        self.screen_loc = (0,0)
        self.leads_to = None
        self.data = [0x00]*12

    def __room_id(self):
        id = self.leads_to.room_id
        l = byte_ops.int_split(id)
        assert(len(l) == 2)
        return l

    def __top_loc(self):
        return self.leads_to.top_loc

    def __screen_loc(self):
        return self.leads_to.screen_loc

    def __bitflag(self):
        bit = 0
        if (self.isElevator):
            bit += 0x80
        if (self.newArea):
            bit += 0x40
        return bit

    def __direction(self):
        dir = self.direction
        if (self.autoClose):
            dir += 4
        return dir

    def __distance(self):
        if (self.direction < 2):
            return (0x80, 00)
        elif (self.direction == 3):
            return (0x01, 0x40)
        else:
            return (0x01, 0xc0)

    def __check_leads_to(self):
        assert(self.leads_to != None)
        assert(self.leads_to.leads_to == self)

    def __update_data(self):
        self.__check_leads_to()
        self.data[2] = self.__bitflag()
        self.data[3] = self.__direction()
        pair = self.__distance()
        self.data[8] = pair[0]
        self.data[9] = pair[1]
        l = self.__room_id()
        self.data[0] = l[0]
        self.data[1] = l[1]
        top = self.__top_loc()
        self.data[4] = top[0]
        self.data[5] = top[1]
        screen = self.__screen_loc()
        self.data[6] = screen[0]
        self.data[7] = screen[1]

    def dataToHex(self):
        self.__update_data()
        return bytes(self.data)

#TODO:
# - PLMs
# - Enemies
# - Scrolls
# - FX
