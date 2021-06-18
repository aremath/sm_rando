from functools import reduce, wraps
import os
import inspect
from . import byte_ops
from .address import *
from .compress import compress

# https://stackoverflow.com/questions/1389180/automatically-initialize-instance-variables
def auto_init(func):
        """
        Automatically assigns the parameters.
        """
        names, varargs, keywords, defaults = inspect.getargspec(func)
        @wraps(func)
        def wrapper(self, *args, **kargs):
            for name, arg in list(zip(names[1:], args)) + list(kargs.items()):
                setattr(self, name, arg)
            for name, default in zip(reversed(names), reversed(defaults)):
                if not hasattr(self, name):
                    setattr(self, name, default)
            func(self, *args, **kargs)
        return wrapper

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
    # pre-allocated pointer_def, or something that's room-specific (or a nullptr)
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

# June 2021 stuff:
# Engine

def parse_engine(obj_def, address, obj_names, rom):
    # Unzip to list of parsers
    parsers = zip(*obj_def)[0]
    objs = []
    for parser in parsers:
        obj, size = parser(address, obj_names, rom)
        objs.append(obj)
        address += Address(size)
    return objs

def compile_engine(obj_def, objs, obj_names, obj_addrs, obj_bytes, rom):
    # Unzip to list of compilers
    compilers = zip(*obj_def)[1]
    all_bytes = []
    for compiler, obj in zip(compilers, objs):
        b = compiler(obj, obj_names, obj_addrs, obj_bytes, rom)
        all_bytes.append(b)
    return all_bytes

def list_def(constructor, terminal):
    parser, compiler = constructor.fns

    def new_parser(address, obj_names, rom):
        out_list = []
        out_size = 0
        while rom.read_from_clean(address, len(terminal)) != terminal:
            obj, size = parser(address)
            out_list.append(obj)
            out_size += size
            address += Address(size)
        size += len(terminal)
        return out_list, size

    def new_compiler(obj, obj_names, addr_objs, obj_bytes, rom, bank):
        assert isinstance(obj, list)
        all_bytes = []
        for o in obj:
            obj_bytes = compiler(obj, obj_names, addr_objs, obj_bytes, rom, bank)
            all_bytes.extend(obj_bytes)
        all_bytes.append(terminal)
        return all_bytes

    return new_parser, new_compiler

def pointer_def(constructor, size, bank=None):
    parser, compiler = constructor.fns

    def new_parser(address, obj_names, rom):
        address_bytes = rom.read_from_clean(address, size)
        address = Address(int.from_bytes(address_bytes, byteorder="little"))
        name = constructor.name_def.format(address)
        if bank is None:
            assert size == 3
        else:
            assert size == 2
            address = address + Address(bank << 16)
        parser(address, obj_names, rom)
        return name, size

    def new_compiler(obj, obj_names, addr_objs, obj_bytes, rom, bank):
        compiler(obj, obj_names, addr_objs, obj_bytes, rom, bank)
        return FutureBytes(obj.name, 2, bank)

    return new_parser, new_compiler

# Actual parsers
#def parse_engine(obj_def, address, obj_names, rom):
#def compile_engine(obj_def, obj, obj_names, obj_addrs, obj_bytes, rom):

def mk_default_fns(constructor, obj_def=None):
    # By default, use the default definition
    if obj_def is None:
        obj_def = constructor.parse_definition()

    def parser(address, obj_names, rom):
        name = constructor.name_def.format(address)
        # Use the address as the name for parsing
        # Already being parsed
        if name in obj_names:
            return
        # Register it first so that it won't be processed twice
        obj_names[name] = None
        # Run the parse engine
        s_objs = parse_engine(obj_def, address, obj_names, rom)
        # Address is the name, the last argument
        s = constructor(*s_objs, address)
        # Return the real value
        obj_names[name] = s

    def compiler(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
        # Already being parsed
        if obj.name in obj_addrs:
            return
        # Register so that it won't be processed twice.
        obj_addrs[obj.name] = None
        obj_bytes = compile_engine(obj_def, obj.list, obj_names, obj_addrs, obj_bytes, rom)
        length = bytes_len(obj_bytes)
        addr = rom.memory.allocate(length, bank)
        # Register the real value
        obj_addrs[obj.name] = addr
        obj_bytes[obj.name] = obj_bytes
    return parser, compiler

# Useful for an optional argument
def parse_nothing(address, obj_names, rom):
    return None, 0

def compile_nothing(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    return b""

nothing_fns = (parse_nothing, compile_nothing)

def parse_int(address, obj_names, rom):
    int_b = rom.read_from_clean(address, 1)
    i = int.from_bytes(int_b, byteorder="little")
    return i, 1

def compile_int(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    int_b = obj.to_bytes(1, byteorder="little")
    return int_b

int_fns = (parse_int, compile_int)

def parse_int2(address, obj_names, rom):
    int_b = rom.read_from_clean(address, 2)
    i = int.from_bytes(int_b, byteorder="little")
    return i, 2

def compile_int2(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    int_b = obj.to_bytes(2, byteorder="little")
    return int_b

int2_fns = (parse_int2, compile_int2)

def parse_condition(addres, obj_names, rom):
    assert False

def compile_condition(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    assert False

condition_fns = (parse_condition, compile_condition)

# Currently parsing asm does nothing - too hard to know which parts of the code are
# relevant + how to repoint. This is certainly an interesting concept though
def parse_asm(address, obj_names, rom):
    return None

def compile_asm(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    return None

asm_fns = (parse_asm, compile_asm)

# Classes

class RomObject(object):
    name_def = None

    def __init__(self):
        assert False

    @property
    def list(self):
        assert False
    
    @staticmethod
    def parse_definition():
        assert False

    def __repr__(self):
        return "{}:{}".format(self.name, self.list)

#TODO: how to force allocation in the pre-defined savestation tables?
class SaveStation(RomObject):
    """
    Save Stations. The roots of the parsing / compilation process.
    """
    name = "save_station_{}"

    @auto_init
    def __init__(self, name):
        self.name = name

    @property
    def list(self):
        pass

    # Definitions
    # These are functions to avoid circular dependency because the parsers are
    # mutually recursive
    # They will by evaluated dynamically
    #TODO: I'm certain there is a better way to do this, but I can't think of what it is
    @staticmethod
    def parse_definition():
        return [
        pointer_def(RoomHeader, 2, bank=0x8F),
        pointer_def(Door, 2, bank=0x83),
        int2_fns, # Save X position, pixels
        int2_fns, # Save Y position, pixels
        int2_fns, # Samus X position, pixels
        int2_fns, # Samus Y position, pixels
        ]
SaveStation.fns = mk_default_fns(SaveStation)

class RoomHeader(RomObject):
    # Need names because two objects can start at the same address
    # e.g. a DoorList and its first Door entry.
    name = "room_header_{}"

    @auto_init
    def __init__(self):
        pass

    @property
    def list(self):
        pass

    @staticmethod
    def parse_definition():
        return [
        int_fns,   # Room Index
        (parse_area_index, compile_area_index),   # Area Index
        int_fns,   # X position on map
        int_fns,   # Y position on map
        int_fns,   # Room width in screens
        int_fns,   # Room height in screens
        int_fns,   # Up scroll (when does the camera move up?)
        int_fns,   # Down scroll (when does the camera move down?)
        int_fns,   # CRE Bitset
        #(parse_cre_bitset, compile_cre_bitset),   # CRE Bitset
        pointer_def(DoorList, bank=0x8F), # Door List Pointer
        StateConditionList.fns, # State Conditions to decide which RoomState to load
        ]

RoomHeader.fns = mk_default_fns(RoomHeader)

class StateCondition(RomObject):
    name = "state_condition_{}"

    @auto_init
    def __init__(self):
        assert False

    @property
    def list(self):
        assert False
    
    @staticmethod
    def parse_definition():
        return [
        condition_fns,
        pointer_def(RoomState.fns, 2, bank=0x8F),
        ]

StateCondition.fns = mk_default_fns(StateCondition)

#TODO: can get away without some of these objects that just store lists
class StateConditionList(RomObject):
    name = "state_condition_list_{}"

    @auto_init
    def __init__(self, conditions, default):
        #TODO: merge into one list?
        self.conditions = conditions
        self.default = default

    @property
    def list(self):
        return [
            self.conditions,
            self.default,
        ]
    
    @staticmethod
    def parse_definition():
        return [
        list_def(StateCondition.fns, b"\xe5\xe6"),
        # Default roomstate is immediately after the end of the others
        RoomState.fns,
        ]

StateConditionList.fns = mk_default_fns(StateConditionsList)

class RoomState(RomObject):
    name = "room_state_{}"

    @auto_init
    def __init__(self):
        pass

    @property
    def list(self):
        pass

    @staticmethod
    def parse_definition():
        return [
        pointer_def(parse_level_data, compile_level_data, 3),
        int_fns,   # Tileset
        int_fns,   # Music data index
        int_fns,   # Music track index
        pointer_def(FX.fns, 2, bank=0x83),    # FX Data
        pointer_def(EnemyList.fns, 2, bank=0xA1),  # The enemies in the room
        pointer_def(EnemyTypes.fns, 2, bank=0xB4),  # The enemy types available in the room
        int_fns,   # Layer 2 scroll X
        int_fns,   # Layer 2 scroll Y
        pointer_def(Scrolls.fns, 2, bank=0x8F), # Scrolls
        pointer_def(XRAY.fns, 2, bank=0x8F), # Special x-ray blocks
        #TODO: 8F is just a guess
        pointer_def(asm_fns, 2, bank=0x8F),  # Main ASM
        pointer_def(PLMList.fns, 2, bank=0x8F),    # PLMs
        #TODO: 8F is just a guess
        pointer_def(Background.fns, 2, bank=0x8F),  # Library background for Layer 2 data
        #TODO: 8F is just a guess
        pointer_def(asm_fns, 2, bank=0x8F),  # Setup ASM
        ]

RoomState.fns = mk_default_fns(RoomState)

class Door(RomObject):
    name = "door_{}"

    @auto_init
    def __init__(self, to_room, elevator_properties, orientation,
            x_pos_low, y_pos_low, x_pos_high, y_pos_high, spawn_distance, asm_pointer):
        self.room_pointer = to_room
        self.elevator_properties = elevator_properties
        self.orientation = orientation
        self.x_pos_low = x_pos_low
        self.y_pos_low = y_pos_low
        self.x_pos_high = x_pos_high
        self.y_pos_high = y_pos_high
        self.spawn_distance = spawn_distance
        self.asm_pointer = asm_pointer

    @property
    def list(self):
        return [
        self.room_pointer,
        self.elevator_properties,
        self.orientation,
        #TODO: instead of low / high, is this door cap position and screen position?
        self.x_pos_low,
        self.y_pos_low,
        self.x_pos_high,
        self.y_pos_high,
        self.spawn_distance,
        self.asm_pointer,
        ]

    @staticmethod
    def parse_definition():
        return [
        pointer_def(RoomHeader.fns, 2, bank=0x8F),
        #TODO special parsers for elevator + orientation
        int_fns,   # Elevator properties
        int_fns,   # Orientation
        int_fns,   # X position low byte
        int_fns,   # Y position low byte
        int_fns,   # X position high byte
        int_fns,   # Y position high byte
        int2_fns, # Distance from door to spawn Samus
        pointer_def(asm_fns, 2, bank=0x8F),   # Door ASM
        ]

Door.fns = mk_default_fns(Door)

class DoorList(RomObject):
    name = "door_list_{}"

    @auto_init
    def __init__(self, l):
        self.l = l

    @property
    def list(self):
        return [self.l]
    
    #TODO: door list might not actually be delimited by \xffs
    @staticmethod
    def parse_definition():
        return [
        list_def(pointer_def(Door.fns, 2, bank=0x83), b"\xff\xff")
        ]

DoorList.fns = mk_default_fns(DoorList)

class FXEntry(RomObject):
    name = "fx_entry_{}"

    @auto_init
    def __init__(self):
        pass

    @property
    def list(self):
        pass

    @staticmethod
    def parse_definition():
        return [
        pointer_def(Door.fns, 2, bank=0x83),
        int2_fns, # Base Y position
        int2_fns, # Target Y position
        int2_fns, # Y Velocity
        int_fns,   # Timer
        int_fns,   # Layer 3 Type #TODO enum
        int_fns,   # Default Layer Blend #TODO enum
        int_fns,   # Layer 3 Layer Blend
        int_fns,   # Liquid options #TODO
        int_fns,   # Palette FX Bitset
        int_fns,   # Animated Tiles Bitset
        int_fns,   # Palette Blend
        ]

FXEntry.fns = mk_default_fns(FXEntry)
# Parse nothing instead of the first pointer
# The \x00\x00 delimiter on the FX list takes the place of this pointer
# in both parsing and compiling
FXEntry.default_fns = mk_default_fns(FXEntry, [nothing_fns] + FXEntry.parse_definition()[1:])

class FX(RomObject):
    name = "fx_{}"

    @auto_init
    def __init__(self):
        pass

    @staticmethod
    def list(self):
        pass
    
    #TODO: how to do \xff\xff "No FX"?
    #TODO: how to do default FX?
    @staticmethod
    def parse_definition():
        return [
        list_def(FXEntry.fns, b"\x00\x00"),
        FXEntry.default_fns
        ]

FX.fns = mk_default_fns(FX)

class EnemyList(RomObject):
    name = "enemy_list_{}"

    # kill_count: Number of enemy deaths needed to clear the current room
    @auto_init
    def __init__(self, enemies, kill_count):
        pass

    @property
    def list(self):
        return [
            self.enemies,
            self.kill_count
        ]
    
    @staticmethod
    def parse_definition():
        return [
        list_def(Enemy.fns, b"\xff\xff"),
        int2_fns
        ]

EnemyList.fns = mk_default_fns(EnemyList)

class Enemy(RomObject):
    name = "enemy_{}"

    @auto_init
    def __init__(self):
        pass

    @property
    def list(self):
        pass

    @staticmethod
    def parse_definition():
        return [
        int2_fns, # Enemy ID #TODO: really is a pointer
        int2_fns, # X Position
        int2_fns, # Y Position
        int2_fns, # Initialization Parameter
        int2_fns, # Properties #TODO enum
        int2_fns, # Properties 2 #TODO enum
        int2_fns, # Parameter 1
        int2_fns, # Parameter 2
        ]

Enemy.fns = mk_default_fns(Enemy)

class EnemyTypes(RomObject):
    name = "enemy_types_{}"

    @auto_init
    def __init__(self, l):
        pass

    @property
    def list(self):
        return [self.l]
    
    @staticmethod
    def parse_definition():
        return [
        list_def(EnemyType.fns, b"\xff\xff")
        ]

EnemyTypes.fns = mk_default_fns(EnemyTypes)

class EnemyType(RomObject):
    name = "enemy_type_{}"

    @auto_init
    def __init__(self):
        assert False

    @property
    def list(self):
        assert False
    
    @staticmethod
    def parse_definition():
        return [
        int2_fns, # Enemy ID #TODO: really is a pointer
        int2_fns, # Palette Index
        ]

EnemyType.fns = mk_default_fns(EnemyType)

class LevelData(RomObject):
    name = "level_data_{}"

    @auto_init
    def __init__(self):
        assert False

    def list(self):
        assert False

    # Level Data does NOT use default fns
    @staticmethod
    def parse_definition():
        assert False

    def parser(self):
        pass

    def compiler(self):
        pass

LevelData.fns = (LevelData.parser, LevelData.compiler)

class PLMList(RomObject):
    name = "PLM_list_{}"

    @auto_init
    def __init__(self, l):
        pass

    def list(self):
        return [self.l]

    @staticmethod
    def parse_definition():
        return [
            list_def(PLM.fns, b"\x00\x00")
        ]

PLMList.fns = mk_default_fns(PLMList)

class PLM(RomObject):
    name = "PLM_{}"

    @auto_init
    def __init__(self, plm_id, xpos, ypos, parameter, name):
        pass

    def list(self):
        return [
            self.plm_id,
            self.xpos,
            self.ypos,
            self.parameter
        ]

    @staticmethod
    def parse_definition():
        return [
            int2_fns,   # PLM ID
            int_fns,    # X Position
            int_fns,    # Y Position
            int2_fns    # PLM Parameter
        ]
        assert False

PLM.fns = mk_default_fns(PLM)

class Scrolls(RomObject):
    name = "scrolls_{}"

    @auto_init
    def __init__(self):
        assert False

    def list(self):
        assert False

    @staticmethod
    def parse_definition():
        assert False

Scrolls.fns = mk_default_fns(Scrolls)

########################### OLD CLASSES ################################

class RoomState(object):
    """A roomstate is a configuration for a room. Corresponds to 'event' in the SMILE guide.
    Every room needs at least one default roomstate, but various events can trigger more. """
    
    def __init__(self, room_id, state_id, event_value, event_arg, level, tileset, song,
            fx, enemies, enemy_set, background_scroll_xy, scrolls, main_asm, plms, background, setup_asm):
        self.state_id = state_id
        self.event_value = event_value
        # Data members that are read in as bytes
        if self.event_value == 0xe5e6:
            self.default_event=True
        else:
            self.default_event=False
        self.event_head = convert_event(event_value, event_arg)
        self.tileset = tileset.to_bytes(1, byteorder='little')
        self.song = song.to_bytes(2, byteorder='little')
        self.background_scrolls = background_scroll_xy[0].to_bytes(1, byteorder='little')
        self.background_scrolls += background_scroll_xy[1].to_bytes(1, byteorder='little')
       
        # Data members that will be allocated then become pointer_defs
        sym_ptr = "room_{}_".format(room_id)
        self.sym_ptr = sym_ptr
        # Future pointer_def to the room header that holds this state
        self.room_head = FutureAddress(sym_ptr + "head")
        # This is a future pointer_def to where the event's state will be within the room header
        self.state_ptr = get_future_ptr(state_id, "state", sym_ptr)
        self.level_data_ptr = get_future_ptr(level, "level", sym_ptr)
        self.fx_ptr = get_future_ptr(fx, "fx", sym_ptr)
        # A note on enemies vs. enemy set: enemies refers to the actual enemies that
        # are present in the room. Enemy set refers to the types of enemies that can be
        # present. Confusingly, these correspond respectively to the "enemy set" and
        # "enemy gfx" pointer_defs that are referred to in the SMILE guide. My naming scheme
        # corresponds to the metconst wiki page, and I think these names are better anyway.
        self.enemies_ptr = get_future_ptr(enemies, "enemies", sym_ptr) 
        self.enemy_set_ptr = get_future_ptr(enemy_set, "enemy_set", sym_ptr) 
        self.scrolls_ptr = get_future_ptr(scrolls, "scrolls", sym_ptr) 
        self.main_asm_ptr = get_future_ptr(main_asm, "main_asm", sym_ptr)
        self.plms_ptr = get_future_ptr(plms, "plms", sym_ptr)
        self.background_ptr = get_future_ptr(background, "background", sym_ptr)
        self.setup_asm_ptr = get_future_ptr(setup_asm, "setup_asm", sym_ptr)

    def to_bytes(self, pos):
        futures = []
        if self.default_event == True:
            head = self.event_head
        # The extra two bytes will be used to store a pointer_def to the rest of the event data
        else:
            head = self.event_head + b"\x00\x00"
            futures.append(FutureAddressWrite(self.state_ptr, self.room_head + mk_future(pos), 2))
        tail = b""
        tail += b"\x00\x00\x00"
        if self.level_data_ptr is not None:
            futures.append(FutureAddressWrite(self.level_data_ptr, self.state_ptr, 3)) # 3
        tail += self.tileset    # 4
        tail += self.song       # 6
        tail += b"\x00\x00"
        if self.fx_ptr is not None:
            futures.append(FutureAddressWrite(self.fx_ptr, self.state_ptr + mk_future(0x6), 2, bank=0x83)) # 8
        tail += b"\x00\x00"
        if self.enemies_ptr is not None:
            futures.append(FutureAddressWrite(self.enemies_ptr, self.state_ptr + mk_future(0x8), 2, bank=0xa1)) # a
        tail += b"\x00\x00"
        if self.enemy_set_ptr is not None:
            futures.append(FutureAddressWrite(self.enemy_set_ptr, self.state_ptr + mk_future(0xa), 2, bank=0xb4)) # c
        tail += self.background_scrolls # e
        tail += b"\x00\x00"
        if self.scrolls_ptr is not None:
            futures.append(FutureAddressWrite(self.scrolls_ptr, self.state_ptr + mk_future(0xe), 2, bank=0x8f)) # 10
        tail += b"\x00\x00" # 12 - special xray stuff - I'm not using it for now
        tail += b"\x00\x00"
        if self.main_asm_ptr is not None:
            futures.append(FutureAddressWrite(self.main_asm_ptr, self.state_ptr + mk_future(0x12), 2, bank=0x8f)) # 14
        tail += b"\x00\x00"
        if self.plms_ptr is not None:
            futures.append(FutureAddressWrite(self.plms_ptr, self.state_ptr + mk_future(0x14), 2, bank=0x8f)) # 16
        tail += b"\x00\x00"
        if self.background_ptr is not None:
            futures.append(FutureAddressWrite(self.background_ptr, self.state_ptr + mk_future(0x16), 2, bank=0x8f)) # 18
        tail += b"\x00\x00"
        if self.setup_asm_ptr is not None:
            futures.append(FutureAddressWrite(self.setup_asm_ptr, self.state_ptr + mk_future(0x18), 2, bank=0x8f)) # 1a
        assert len(tail) == 26, len(tail)
        return head, tail, futures

def alloc_and_collect(a_list, memory, env):
    """Allocates a list of allocateable objects to memory.
        Returns a list of the resulting future addresses that must
        be filled."""
    f_list = map(lambda x: x.allocate(memory, env), a_list)
    # Un-wrap the futures (take [[future]] -> [future])
    return [future for fs in f_list for future in fs]

# defaults:
# up_scroll = 0x90
# down_scroll = 0xa0
# special graphics = 0
#TODO: some way for door data to be shared
# (for a door to be a symbolic pointer_def string instead of a Door)
class RoomHeader(object):
    """Represents a room header (including any data that the header relies on)"""

    def __init__(self, room_id, room_index, room_area, map_xy, room_size_xy, up_scroll, down_scroll,
            special_graphics, room_states, levels, fxs, enemies, enemy_sets,
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
        self.room_states = room_states  # alloced as a part of self.allocate
        self.levels = levels            # banks c3-ce (not technically bank restricted)
        self.fxs = fxs                  # bank 83
        self.enemies = enemies          # bank a1
        self.enemy_sets = enemy_sets    # bank b4
        self.scrolls = scrolls          # bank 8f
        self.main_asms = main_asms      # bank 8f
        self.plms = plms                # bank 8f
        self.setup_asms = setup_asms    # bank 8f
        self.doors = doors              # bank 83

        # Important (future) pointer_defs
        sym_ptr = "room_{}_".format(room_id)
        self.sym_ptr = sym_ptr
        self.header_ptr = FutureAddress(sym_ptr + "head")
        self.doors_ptr = FutureAddress(sym_ptr + "doors")

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
        # Write at the end of the header a future pointer_def to where the doors are placed
        futures.append(FutureAddressWrite(self.doors_ptr, self.header_ptr + mk_future(0x9), 2, bank=0x8f))
        assert len(head) == 11
        return head, futures

    def allocate(self, memory, env):
        #### Layout ####
        # 11 Standard bytes
        # 5 (?) extra bytes per Event
        # 28 standard bytes
        # 26 extra bytes per event
        # 2 bytes per door

        futures = []
        # Allocate levels, fxs, enemies, enemy_sets, scrolls, main_asms, plms, setup_asms, doors
        futures.extend(alloc_and_collect(self.levels, memory, env))
        futures.extend(alloc_and_collect(self.fxs, memory, env))
        futures.extend(alloc_and_collect(self.enemies, memory, env))
        futures.extend(alloc_and_collect(self.enemy_sets, memory, env))
        futures.extend(alloc_and_collect(self.scrolls, memory, env))
        futures.extend(alloc_and_collect(self.main_asms, memory, env))
        futures.extend(alloc_and_collect(self.plms, memory, env))
        futures.extend(alloc_and_collect(self.setup_asms, memory, env))
        futures.extend(alloc_and_collect(self.doors, memory, env))
        print(futures)
        
        # Generate to_bytes() using head_bytes, then room_states bytes, then FutureWrites for door ptrs
        out = b""
        b, f = self.head_bytes()
        futures.extend(f)
        out += b
        pos = len(out)
        tails = []
        # Add the states to the byte representation -- keep their tails since the next part of
        # the room header is just the list of headers
        for state in self.room_states:
            hb, tb, f = state.to_bytes(pos)
            futures.extend(f)
            out += hb
            pos = len(out)
            # Use prepend so that the default events tail lines up properly
            tails.insert(0, (state.state_id, tb))
        # Need the last state to be the default state
        assert state.event_value == 0xe5e6, "Last state is not default"
        # Now add the state tails
        for sid, tail in tails:
            # Now we know where each state is relative to the room header -- add that
            # info to env
            env[self.sym_ptr + "state_{}".format(sid)] = self.header_ptr + mk_future(pos)
            out += tail
            pos = len(out)
        # Now we know where the doors start -- add that to env
        env[self.sym_ptr + "doors"] = self.header_ptr + mk_future(pos)
        for door in self.doors:
            # Add a future write to each door
            futures.append(FutureAddressWrite(door.from_sym_ptr, self.header_ptr + mk_future(pos), 2, bank=0x83))
            out += b"\x00\x00"
            pos = len(out)
        # Allocate self with size of to_bytes
        addr = memory.allocate_and_write(out, [0x8f])
        env[self.sym_ptr + "head"] = addr
        # Return the addr for room_mdb
        return addr, futures

class LevelData(object):
    """ Contains all the level data (just a giant array of bytes) including
        the background data if need be """

    def __init__(self, room_id, level_id, level_data):
        self.sym = "room_{}_level_{}".format(room_id, level_id)
        self.level_data = level_data

    def get_compressed(self):
        return compress.compress(self.dataToHex())

    def allocate(self, memory, env):
        to_write = self.get_compressed()
        #TODO: don't hardcode this - need a file here to keep
        # rom-specific global-type things
        addr = memory.allocate_and_write(self, range(0xc3,0xce))
        env[self.sym] = addr
        return []

def direction_convert(close, s):
    """Convert a door direction as a string to the ROM representation.
        close is whether the door closes when you leave it."""
    if s == "L":
        d = 1
    elif s == "R":
        d = 0
    elif s == "D":
        d = 2
    elif s == "U":
        d = 3
    else:
        assert False, "Bad direction string!"
    return 4*close + d

#TODO: a "classier" data structure for this
class FX(object):

    def __init__(self, room_id, fx_id, door_select, liquid_start, liquid_new,
            liquid_speed, liquid_delay, fx_type, fx_a, fx_b, fx_c, palette_bitflag,
            tile_bitflag, palette_blend):
        self.sym = "room_{}_fx_{}".format(room_id, fx_id)
        self.sym_ptr = FutureAddress(self.sym)
        if door_select is not None:
            rid, did = door_select
            door_sym = "room_{}_door_{}".format(rid, did)
            self.door_sym_ptr = FutureAddress(door_sym)
        else:
            self.door_sym_ptr = None
        self.liquid_start = liquid_start.to_bytes(2, byteorder='little')
        self.liquid_new = liquid_new.to_bytes(2, byteorder='little')
        self.liquid_speed = liquid_speed.to_bytes(2, byteorder='little')
        self.liquid_delay = liquid_delay.to_bytes(2, byteorder='little')
        self.fx_type = fx_type.to_bytes(1, byteorder='little')
        self.fx_a = fx_a.to_bytes(1, byteorder='little')
        self.fx_b = fx_b.to_bytes(1, byteorder='little')
        self.fx_c = fx_c.to_bytes(1, byteorder='little')
        self.palette_bitflag = palette_bitflag.to_bytes(1, byteorder='little')
        self.tile_bitflag = tile_bitflag.to_bytes(1, byteorder='little')
        self.palette_blend = palette_blend.to_bytes(1, byteorder='little')

    def to_bytes(self):
        futures = []
        out = b""
        if self.door_sym_ptr is not None:
            futures.append(FutureAddressWrite(self.door_sym_ptr, self.sym_ptr, 2, 0x83))
        out += b"\x00\x00"
        out += self.liquid_start
        out += self.liquid_new
        out += self.liquid_speed
        out += self.liquid_delay
        out += self.fx_type
        out += self.fx_a
        out += self.fx_b
        out += self.fx_c
        out += self.palette_bitflag
        out += self.tile_bitflag
        out += self.palette_blend
        return out, futures

    def allocate(self, memory, env):
        to_write, fs = self.to_bytes()
        addr = memory.allocate_and_write(to_write, [0x83])
        env[self.sym] = addr
        return fs

def list_to_bytes(l):
    return reduce(lambda x,y: x+y, map(lambda z: z.to_bytes(), l))

class PLMSet(object):

    def __init__(self, room_id, plm_set_id, plms):
        self.sym = "room_{}_plms_{}".format(room_id, plm_set_id)
        self.plms = plms

    def to_bytes(self):
        plm_bytes = list_to_bytes(self.plms)
        return plm_bytes + b"\x00\x00"
        
    def allocate(self, memory, env):
        to_write = self.to_bytes()
        addr = memory.allocate_and_write(to_write, [0x8f])
        env[self.sym] = addr
        return []

class PLM(object):

    def __init__(self, plm_id, xy, arg):
        self.plm_id = plm_id.to_bytes(2, byteorder='little')
        self.x = xy[0].to_bytes(1, byteorder='little')
        self.y = xy[1].to_bytes(1, byteorder='little')
        self.arg = arg.to_bytes(2, byteorder='little')
        
    def to_bytes(self):
        out = b""
        out += self.plm_id
        out += self.x
        out += self.y
        out += self.arg
        return out

#TODO: scrolls seem easily shareable between rooms

class Scrolls(object):

    def __init__(self, room_id, scroll_id, scroll_data):
        self.sym = "room_{}_scrolls_{}".format(room_id, scrolls_id)
        self.scroll_data = scroll_data

    def allocate(self, memory, env):
        to_write = self.scroll_data
        addr = memory.allocate_and_write(to_write, [0x8f])
        env[self.sym] = addr
        return []

class Enemies(object):

    def __init__(self, room_id, enemies_id, enemies):
        self.sym = "room_{}_enemies_{}".format(room_id, enemies_id)
        self.enemies = enemies

    def to_bytes(self):
        enemy_bytes = list_to_bytes(self.enemies)
        return enemy_bytes + "\xff\xff"

    def allocate(self, memory, env):
        to_write = self.to_bytes()
        addr = memory.allocate_and_write(to_write, [0xa1])
        env[self.sym] = addr
        return []

class Enemy(object):

    def __init__(self, enemy_id, xy, tilemaps, special, graphics, speed, speed2):
        self.enemy_id = enemy_id.to_bytes(2, byteorder='little')
        self.x = xy[0].to_bytes(2, byteorder='little')
        self.y = xy[1].to_bytes(2, byteorder='little')
        self.tilemaps = tilemaps.to_bytes(2, byteorder='little')
        self.special = special.to_bytes(2, byteorder='little')
        self.graphics = graphics.to_bytes(2, byteorder='little')
        self.speed = speed.to_bytes(2, byteorder='little')
        self.speed2 = speed2.to_bytes(2, byteorder='little')

    def to_bytes(self):
        out = b""
        out += self.enemy_id
        out += self.x
        out += self.y
        out += self.tilemaps
        out += self.special
        out += self.graphics
        out += self.speed
        out += self.speed2
        return out

#TODO: it occurs to me now that it might be good to pair enemy sets with enemies
# It's possible to have an enemy list which is not compatible with a given enemy set.

class EnemySet(object):

    def __init__(self, room_id, enemy_set_id, enemy_palettes):
        self.sym = "room_{}_enemy_set_{}".format(room_id, enemy_set_id)
        assert len(enemy_palettes) <= 4
        self.enemy_palettes = enemy_palettes

    def to_bytes(self):
        palette_bytes = list_to_bytes(self.enemy_palettes)
        return out + "\xff\xff"

    #TODO: this seems like a place where it would be useful to have a superclass
    # for "types of things that get allocated"
    def allocate(self, memory, env):
        to_write = self.to_bytes()
        addr = memory.allocate_and_write(to_write, [0xb4])
        env[self.sym] = addr
        return []

class EnemyPalette(object):

    def __init__(self, enemy_id, enemy_palette):
        assert enemy_palette in [1, 2, 3, 7]
        self.enemy_id = enemy_id.to_bytes(2, byteorder='little')
        self.enemy_palette = enemy_palette.to_bytes(2, byteorder='little')

    def to_bytes(self):
        out = b""
        out += self.enemy_id
        out += self.enemy_palette
        return out

