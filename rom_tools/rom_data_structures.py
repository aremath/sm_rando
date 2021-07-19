from functools import reduce, wraps
import inspect
from enum import IntEnum
import numpy as np

from . import byte_ops
from .address import *
from .compress import compress
from .compress import decompress

# https://stackoverflow.com/questions/1389180/automatically-initialize-instance-variables
def auto_init(func):
        """
        Automatically assigns the parameters of a class.
        """
        names, varargs, keywords, defaults = inspect.getargspec(func)

        @wraps(func)
        def wrapper(self, *args, **kargs):
            for name, arg in list(zip(names[1:], args)) + list(kargs.items()):
                setattr(self, name, arg)
            if defaults is not None:
                for name, default in zip(reversed(names), reversed(defaults)):
                    if not hasattr(self, name):
                        setattr(self, name, default)
            func(self, *args, **kargs)
        return wrapper

class Event(IntEnum):
    ZebesAwake = 0
    MetroidAteSidehopper = 1
    MotherBrainGlassBroken = 2
    # Zebetites Destroyed
    Zebetite1 = 3
    Zebetite2 = 4
    Zebetite3 = 5
    PhantoonStatue = 6
    RidleyStatue = 7
    DraygonStatue = 8
    KraidStatue = 9
    TourianUnlocked = 10
    MaridiaTubeBroken = 11
    AcidLowered = 12
    ShaktoolPath = 13
    TimebombSet = 14
    AnimalsSaved = 15
    # Metroid Rooms Cleared
    Metroid1 = 16
    Metroid2 = 17
    Metroid3 = 18
    Metroid4 = 19
    Unused = 20
    SpeedBoosterLavaquakeCleared = 21
    # Rest unused.

# Why is mother brain a miniboss?
class BossSettings(IntEnum):
    AreaBoss = 1        # (Kraid, Phantoon, Draygon, both Ridleys)
    AreaMiniboss = 2    # (Spore Spawn, Botwoon, Crocomire, Mother Brain)
    AreaTorizo = 4      # (Bomb Torizo, Golden Torizo)

class Condition(IntEnum):
    Default = 0xE5E6
    DoorCheck = 0xE5Eb  # 2-byte door pointer argument, used if the player entered from that door
    AreaBossDefeated = 0xE5FF # If the main boss of the room area is dead
    Event = 0xE612      # 1 byte event argument, used if that event is set (See Event)
    BossDefeated = 0xE629   # 1-byte argument, used if ANY of the boss bits for the room area are set.
    MorphBall = 0xE640
    MorphBallMissies = 0xE652
    PowerBombs = 0xE669
    SpeedBooster = 0xE678

class Area(IntEnum):
    Crateria = 0
    Brinstar = 1
    Norfair = 2
    Wrecked_Ship = 3
    Maridia = 4
    Tourian = 5
    Ceres = 6
    Debug = 7

class CRESettings(IntEnum):
    DisableLayer1 = 1
    ReloadCRE = 2
    LoadLargeTileset = 4

class ScrollValue(IntEnum):
    RedScroll = 0
    BlueScroll = 1
    GreenScroll = 2

# Engine

def parse_engine(obj_def, address, obj_names, rom, data):
    total_size = 0
    # Unzip to list of parsers
    if len(obj_def) == 0:
        parsers = []
    else:
        parsers = list(zip(*obj_def))[0]
    objs = []
    for i, parser in enumerate(parsers):
        if len(obj_def[i]) == 3:
            data_fun = obj_def[i][2]
            new_data = data_fun(data, objs)
        else:
            new_data = None
        print("Using {} at {}".format(parser.__name__, address))
        obj, size = parser(address, obj_names, rom, new_data)
        print("Got: {}, Size: {} using {} at {}\n".format(obj, size, parser.__name__, address))
        objs.append(obj)
        address += Address(size)
        total_size += size
    return objs, total_size

def compile_engine(obj_def, objs, obj_names, obj_addrs, obj_bytes, rom):
    # Unzip to list of compilers
    if len(obj_def) == 0:
        compilers = []
    else:
        compilers = list(zip(*obj_def))[1]
    all_bytes = []
    for compiler, obj in zip(compilers, objs):
        b = compiler(obj, obj_names, obj_addrs, obj_bytes, rom)
        all_bytes.append(b)
    return all_bytes

def list_def(fns, terminal, terminal_cond=None):
    parser, compiler = fns
    if terminal_cond is not None:
        assert terminal is None
    else:
        terminal_cond = lambda address, rom: (rom.read_from_clean(address, len(terminal)) != terminal)

    def list_parser(address, obj_names, rom, data):
        out_list = []
        out_size = 0
        while terminal_cond(address, rom):
            obj, size = parser(address, obj_names, rom, data)
            out_list.append(obj)
            out_size += size
            address += Address(size)
        # Include the terminal in the size if it's not used as a condition
        if terminal is not None:
            out_size += len(terminal)
        return out_list, out_size

    def list_compiler(obj, obj_names, addr_objs, obj_bytes, rom, bank):
        assert isinstance(obj, list)
        all_bytes = []
        for o in obj:
            obj_bytes = compiler(obj, obj_names, addr_objs, obj_bytes, rom, bank)
            all_bytes.extend(obj_bytes)
        all_bytes.append(terminal)
        return all_bytes

    return list_parser, list_compiler

def pointer_def(constructor, size, bank=None, invalid_bytes=None, invalid_ok=False):
    parser, compiler = constructor.fns

    def pointer_parser(address, obj_names, rom, data):
        address_bytes = rom.read_from_clean(address, size)
        address_int = int.from_bytes(address_bytes, byteorder="little")
        if invalid_bytes is not None and address_bytes == invalid_bytes:
            return None, size
        #print(address_bytes)
        print(hex(address_int))
        # If invalid pointers are ok, call the parser on the raw integer
        # We will trust the parser to handle things properly
        if invalid_ok:
            if bank is None:
                address = address_int
            else:
                address = address_int + (bank << 16)
        elif bank is None:
            assert size == 3
            address = Address(address_int, mode="snes")
        else:
            assert size == 2
            address = Address(address_int, mode="snes")
            address = address + Address((bank << 16) + 0x8000, mode="snes")
        #print(hex(address.as_pc))
        name = constructor.name_def.format(address)
        parser(address, obj_names, rom, data)
        return name, size

    def pointer_compiler(obj, obj_names, addr_objs, obj_bytes, rom, bank):
        if invalid_bytes is not None and obj is None:
            return invalid_bytes
        compiler(obj, obj_names, addr_objs, obj_bytes, rom, bank)
        return FutureBytes(obj.name, 2, bank)

    return pointer_parser, pointer_compiler

# Actual parsers
#def parse_engine(obj_def, address, obj_names, rom):
#def compile_engine(obj_def, obj, obj_names, obj_addrs, obj_bytes, rom):

def parse_wrapper(constructor):
    """
    Responsible for all the bookkeeping associated with parsing an object
    The inner function should only return the list of object args (while recursively calling other parsers)
    """
    def inner(func):
        @wraps(func)
        def wrapper(address, obj_names, rom, data):
            name = constructor.name_def.format(address)
            # Use the address as the name for parsing
            # Already being parsed
            if name in obj_names:
                return
            # Register it first so that it won't be processed twice
            obj_names[name] = None
            print("Parsing: {}".format(name))
            s_objs, size = func(address, obj_names, rom, data)
            print(constructor)
            print(s_objs)
            print("Done Parsing: {}".format(name))
            # Address is the name, the last argument
            s = constructor(*s_objs, address)
            # Register the real value
            obj_names[name] = s
            return name, size
        return wrapper
    return inner

def compile_wrapper(func):
    """
    Responsible for all the bookkeeping associated with compiling an object
    The inner function should only return the object bytes (while recursively calling other compilers)
    """
    @wraps(func)
    def wrapper(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
        # Already being compiled
        if obj.name in obj_bytes:
            return
        # Register so that it won't be processed twice.
        obj_bytes[obj.name] = None
        print("Compiling: {}".format(obj.name))
        this_obj_bytes = func(obj, obj_names, obj_addrs, obj_bytes, rom, bank)
        length = bytes_len(this_obj_bytes)
        # Register the real value
        # Skip addrs if it's preallocated
        #TODO: for each object, if it has a "name",
        # just allocate it where it was before
        if obj not in obj_addrs:
            addr = rom.memory.allocate(length, bank)
            obj_addrs[obj.name] = addr
        else:
            assert obj_addrs[obj.name].bank == bank
        obj_bytes[obj.name] = this_obj_bytes
    return wrapper

def mk_default_fns(constructor, obj_def=None):
    # By default, use the default definition
    if obj_def is None:
        obj_def = constructor.parse_definition

    @parse_wrapper(constructor)
    def parser(address, obj_names, rom, data):
        return parse_engine(obj_def(), address, obj_names, rom, data)

    @compile_wrapper
    def compiler(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
        return compile_engine(obj_def(), obj.list, obj_names, obj_addrs, obj_bytes, rom)

    return parser, compiler

# Useful for an optional argument
def parse_nothing(address, obj_names, rom, data):
    return None, 0

def compile_nothing(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    return b""

nothing_fns = (parse_nothing, compile_nothing)

def parse_int(address, obj_names, rom, data):
    int_b = rom.read_from_clean(address, 1)
    i = int.from_bytes(int_b, byteorder="little")
    return i, 1

def compile_int(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    int_b = obj.to_bytes(1, byteorder="little")
    return int_b

int_fns = (parse_int, compile_int)

def parse_int2(address, obj_names, rom, data):
    int_b = rom.read_from_clean(address, 2)
    i = int.from_bytes(int_b, byteorder="little")
    return i, 2

def compile_int2(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    int_b = obj.to_bytes(2, byteorder="little")
    return int_b

#TODO: tuple_fns for x, y pairs
int2_fns = (parse_int2, compile_int2)

def parse_condition(address, obj_names, rom, data):
    assert False

def compile_condition(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    assert False

condition_fns = (parse_condition, compile_condition)

def mk_enum_fns(under_fns, enum):
    under_parser, under_compiler = under_fns
    def enum_parser(address, obj_names, rom, data):
        p, n = under_parser(address, obj_names, rom, data)
        for e in enum:
            if e == p:
                return e, n
        assert False, "No Matching Enum Entry"
    def enum_compiler(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
        # Can simply call the under-parser for an IntEnum
        under_compiler(obj, obj_names, obj_addrs, obj_bytes, rom, bank)
    return enum_parser, enum_compiler

area_index_fns = mk_enum_fns(int_fns, Area)
parse_condition, compile_condition = mk_enum_fns(int2_fns, Condition)
event_fns = mk_enum_fns(int_fns, Event)

def mk_bitset_fns(under_fns, enum):
    under_parser, under_compiler = under_fns
    def enum_parser(address, obj_names, rom, data):
        s = set()
        p, n = under_parser(address, obj_names, rom, data)
        for e in enum:
            if e & p:
                s.add(e)
        # Size is the number of bytes grabbed by the under parser
        return s, n
    def enum_compiler(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
        i = 0
        for e in enum:
            i &= e
        under_compiler(i, obj_names, obj_addrs, obj_bytes, rom, bank)
    return enum_parser, enum_compiler

cre_set_fns = mk_bitset_fns(int_fns, CRESettings)
boss_set_fns = mk_bitset_fns(int_fns, BossSettings)

# This is a function instead of a dictionary because Door hasn't been defined yet
def get_cond_arg_fns(condition):
    if condition is Condition.Default:
        return nothing_fns
    elif condition is Condition.DoorCheck:
        return pointer_def(Door, 2, bank=0x83),
    elif condition is Condition.AreaBossDefeated:
        return nothing_fns
    elif condition is Condition.Event:
        return event_fns
    elif condition is Condition.BossDefeated:
        return boss_set_fns
    elif condition is Condition.MorphBall:
        return nothing_fns
    elif condition is Condition.MorphBallMissiles:
        return nothing_fns
    elif condition is Condition.PowerBombs:
        return nothing_fns
    elif condition is Condition.SpeedBooster:
        return nothing_fns
    else:
        assert False, "Bad Condition Type: {}".format(condition)

def parse_state_condition(address, obj_names, rom, data):
    cond, size = parse_condition(address, obj_names, rom, data)
    arg_fns = get_cond_arg_fns(cond)
    arg_parser = arg_fns[0]
    arg_address = address + Address(size)
    arg, arg_size = arg_parser(arg_address, obj_names, rom, data)
    return (cond, arg), (size + arg_size)

def compile_state_condition(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    cond, arg = obj
    cond_bytes = compile_condition(cond, obj_names, obj_addrs, obj_bytes, rom, bank)
    arg_fns = get_cond_arg_fns(cond)
    arg_compiler = arg_fns[1]
    arg_bytes = arg_compiler(arg, obj_names, obj_addrs, obj_bytes, rom, bank)
    return cond_bytes + arg_bytes

state_condition_fns = (parse_state_condition, compile_state_condition)

#TODO:
# Door Orientation (enum with extra bit to indicate door cap closing)
# Tileset       enum
# Music Index   enum
# Track Index   enum
# FX Layer 3    enum
# FX Layer blend    enum
# FX Liquid settings    bitset
# Enemy properties  bitset
# Enemy Extra properties    bitset
# Scroll    enum
# Special X-Ray blocks

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

# Placeholder class for something we don't know how to parse yet
# Currently parsing asm does nothing - too hard to know which parts of the code are
# relevant + how to repoint. This is certainly an interesting concept though
class Placeholder(RomObject):
    name_def = "placeholder_{}"

    def __init__(self, name):
        self.name = name

    @property
    def list(self):
        return []
    
    @staticmethod
    def parse_definition():
        return []

    def __repr__(self):
        return "{}:{}".format(self.name, self.list)

Placeholder.fns = mk_default_fns(Placeholder)

#TODO: how to force allocation in the pre-defined savestation tables?
class SaveStation(RomObject):
    """
    Save Stations. The roots of the parsing / compilation process.
    """
    name_def = "save_station_{}"

    @auto_init
    def __init__(self, room, door, save_x, save_y, samus_x, samus_y, name):
        self.name = name

    @property
    def list(self):
        return [self.name, self.room, self.door, self.save_x, self.save_y, self.samus_x, self.samus_y]

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

def get_room_dims(data, objs):
    return (objs[4], objs[5])

def data_pass(data, objs):
    return data

class RoomHeader(RomObject):
    # Need names because two objects can start at the same address
    # e.g. a DoorList and its first Door entry.
    name_def = "room_header_{}"

    @auto_init
    def __init__(self, room_index, area_index, map_x, map_y, width, height, scroll_up, scroll_down, CRE_bitset, door_list, state_chooser, name):
        pass

    @property
    def list(self):
        return [self.room_index, self.area_index, self.map_x, self.map_y, self.width, self.height,
                self.scroll_up, self.scroll_down, self.CRE_bitset, self.door_list, self.state_chooser]

    @staticmethod
    def parse_definition():
        return [
        int_fns,   # Room Index
        area_index_fns, # Area Index
        int_fns,   # X position on map
        int_fns,   # Y position on map
        int_fns,   # Room width in screens
        int_fns,   # Room height in screens
        int_fns,   # Up scroll (when does the camera move up?)
        int_fns,   # Down scroll (when does the camera move down?)
        cre_set_fns,   # CRE Bitset
        pointer_def(DoorList, 2, bank=0x8F), # Door List Pointer
        (*StateChooser.fns, get_room_dims), # State Conditions to decide which RoomState to load
        ]

RoomHeader.fns = mk_default_fns(RoomHeader)

class StateChoice(RomObject):
    name_def = "state_condition_{}"

    @auto_init
    def __init__(self, state_condition, state, name):
        pass

    @property
    def list(self):
        return [self.state_condition, self.state]
    
    @staticmethod
    def parse_definition():
        return [
        state_condition_fns,
        (*pointer_def(RoomState, 2, bank=0x8F), data_pass),
        ]

StateChoice.fns = mk_default_fns(StateChoice)

#TODO: can get away without some of these objects that just store lists
class StateChooser(RomObject):
    name_def = "state_chooser_{}"

    @auto_init
    def __init__(self, conditions, default, name):
        #TODO: merge into one list?
        pass

    @property
    def list(self):
        return [
            self.conditions,
            self.default,
        ]
    
    @staticmethod
    def parse_definition():
        return [
        # Pass data (which is room dimensions) through
        # \xe6\xe5 because little endian
        (*list_def(StateChoice.fns, b"\xe6\xe5"), data_pass),
        # Default roomstate is immediately after the end of the others
        (*RoomState.fns, data_pass),
        ]

StateChooser.fns = mk_default_fns(StateChooser)

class RoomState(RomObject):
    name_def = "room_state_{}"

    @auto_init
    def __init__(self, level_data, tileset, music_data, music_track, fx, enemy_list, enemy_types,
            layer2_scroll_x, layer2_scroll_y, scrolls, special_xray, main_asm, plms, background_index, setup_asm,
            name):
        pass

    @property
    def list(self):
        return [self.level_data, self.tileset, self.music_data, self.music_track, self.fx,
                self.enemy_list, self.enemy_types, self.layer2_scroll_x, self.layer2_scroll_y,
                self.scrolls, self.special_xray, self.main_asm, self.plms, self.background_index, self.setup_asm]

    @staticmethod
    def parse_definition():
        return [
        (*pointer_def(LevelData, 3), data_pass),# Level Data
        int_fns,                                # Tileset
        int_fns,                                # Music data index
        int_fns,                                # Music track index
        pointer_def(FX, 2, bank=0x83),          # FX Data
        pointer_def(EnemyList, 2, bank=0xA1),   # The enemies in the room
        pointer_def(EnemyTypes, 2, bank=0xB4),  # The enemy types available in the room
        int_fns,                                # Layer 2 scroll X
        int_fns,                                # Layer 2 scroll Y
        #TODO: if this pointer is 0000 it means all blue scrolls
        #TODO: if this pointer is 0001 it means all green scrolls
        (*pointer_def(Scrolls, 2, bank=0x8F, invalid_ok=True), data_pass), # Scrolls
        pointer_def(Placeholder, 2, bank=0x8F, invalid_bytes=b"\x00\x00"), # Special x-ray blocks
        #TODO: 8F is just a guess
        pointer_def(Placeholder, 2, bank=0x8F, invalid_bytes=b"\x00\x00"), # Main ASM
        pointer_def(PLMList, 2, bank=0x8F),     # PLMs
        #TODO: 8F is just a guess
        pointer_def(Placeholder, 2, bank=0x8F, invalid_bytes=b"\x00\x00"),  # Library background for Layer 2 data
        #TODO: 8F is just a guess
        pointer_def(Placeholder, 2, bank=0x8F), # Setup ASM
        ]

RoomState.fns = mk_default_fns(RoomState)

class Door(RomObject):
    name_def = "door_{}"

    @auto_init
    def __init__(self, to_room, elevator_properties, orientation,
            x_pos_low, y_pos_low, x_pos_high, y_pos_high, spawn_distance, asm_pointer, name):
        pass

    @property
    def list(self):
        return [
        self.to_room,
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
        pointer_def(RoomHeader, 2, bank=0x8F),
        #TODO special parsers for elevator + orientation
        int_fns,   # Elevator properties
        int_fns,   # Orientation
        int_fns,   # X position low byte
        int_fns,   # Y position low byte
        int_fns,   # X position high byte
        int_fns,   # Y position high byte
        int2_fns, # Distance from door to spawn Samus
        pointer_def(Placeholder, 2, bank=0x8F, invalid_bytes=b"\x00\x00"),   # Door ASM
        ]

Door.fns = mk_default_fns(Door)

# A door list doesn't have a terminal
# Instead, it's over when we run out of valid addresses
def door_list_check(address, rom):
    b = rom.read_from_clean(address, 2)
    i = int.from_bytes(b, byteorder="little")
    return byte_ops.valid_snes(i)

#TODO: Elevators
class DoorList(RomObject):
    name_def = "door_list_{}"

    @auto_init
    def __init__(self, l, name):
        pass

    @property
    def list(self):
        return [self.l]
    
    #TODO: door list might not actually be delimited by \xffs
    @staticmethod
    def parse_definition():
        return [
        list_def(pointer_def(Door, 2, bank=0x83), None, door_list_check)
        ]

DoorList.fns = mk_default_fns(DoorList)

class FXEntry(RomObject):
    name_def = "fx_entry_{}"

    @auto_init
    def __init__(self, door, liquid_y, liquid_target_y, liquid_speed, liquid_timer,
            layer3_type, default_layer_blend, layer3_blend, liquid_options, palette_fx_bits,
            animated_tiles_bits, palette_blend, name):
        pass

    @property
    def list(self):
        return [self.door, self.liquid_y, self.liquid_target_y, self.liquid_speed,
                self.liquid_timer, self.layer3_type, self.default_layer_blend, self.layer3_blend,
                self.liquid_options, self.palette_fx_bits, self.animated_tiles_bits, self.palette_blend]

    @staticmethod
    def parse_definition():
        return [
        pointer_def(Door, 2, bank=0x83),
        int2_fns, # Liquid Base Y position
        int2_fns, # Liquid Target Y position
        int2_fns, # Liquid Y Velocity (speed)
        int_fns,   # Liquid Timer
        # Liquid begins at the base Y, then rises (or lowers) to the target Y at the speed of the Y vel
        int_fns,   # Layer 3 Type #TODO enum
        int_fns,   # Default Layer Blend #TODO enum
        int_fns,   # Layer 3 Layer Blend
        int_fns,   # Liquid options #TODO enum
        int_fns,   # Palette FX Bitset
        int_fns,   # Animated Tiles Bitset
        int_fns,   # Palette Blend
        ]

FXEntry.fns = mk_default_fns(FXEntry)
# Parse nothing instead of the first pointer
# The \x00\x00 delimiter on the FX list takes the place of this pointer
# in both parsing and compiling
FXEntry.default_fns = mk_default_fns(FXEntry, lambda: [nothing_fns] + FXEntry.parse_definition()[1:])

class FX(RomObject):
    name_def = "fx_{}"

    @auto_init
    def __init__(self, fx_l, default_fx, name):
        pass

    @staticmethod
    def list(self):
        return [self.fx_l, self.default_fx]
    
    #TODO: how to do \xff\xff "No FX"?
    @staticmethod
    def parse_definition():
        return [
        list_def(FXEntry.fns, b"\x00\x00"),
        FXEntry.default_fns
        ]

# Special case: FX of \xff\xff means no FX
@parse_wrapper(FX)
def fx_parser(address, obj_names, rom, data):
    if rom.read_from_clean(address, 2) == b"\xff\xff":
        return [[], None], 2
    else:
        return parse_engine(FX.parse_definition(), address, obj_names, rom, data)

#TODO: can combine these pointers!
@compile_wrapper
def fx_compiler(obj, obj_names, obj_addrs, obj_bytes, rom, bank):
    if len(obj.fx_l) == 0 and obj.default_fx is None:
        return b"\xff\xff"
    else:
        return compile_engine(FX.parse_definition(), obj.list, obj_names, obj_addrs, obj_bytes, rom)

FX.fns = (fx_parser, fx_compiler)

class EnemyList(RomObject):
    name_def = "enemy_list_{}"

    # kill_count: Number of enemy deaths needed to clear the current room
    @auto_init
    def __init__(self, enemies, kill_count, name):
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
        list_def(Enemy.fns, b"\xff\xff"), # Enemies in the room
        int_fns # Number of enemy deaths needed to clear the room (used for grey doors?)
        ]

EnemyList.fns = mk_default_fns(EnemyList)

class Enemy(RomObject):
    name_def = "enemy_{}"

    @auto_init
    def __init__(self, enemy_id, x_pos, y_pos, init_param, properties1, properties2, parameter1, parameter2, name):
        pass

    @property
    def list(self):
        return [self.enemy_id,
                self.x_pos, self.y_pos,
                self.init_param, self.properties1, self.properties2,
                self.parameter1, self.parameter2]

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
    name_def = "enemy_types_{}"

    @auto_init
    def __init__(self, l, name):
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
    name_def = "enemy_type_{}"

    @auto_init
    def __init__(self, enemy_id, palette_index, name):
        pass

    @property
    def list(self):
        return [self.enemy_id, self.palette_index, name]
    
    @staticmethod
    def parse_definition():
        return [
        int2_fns, # Enemy ID #TODO: really is a pointer
        int2_fns, # Palette Index
        ]

EnemyType.fns = mk_default_fns(EnemyType)

class LevelData(RomObject):
    name_def = "level_data_{}"

    #TODO: level1, level2, bts as arrays of bytes
    @auto_init
    def __init__(self, level_bytes, name):
        pass

    def list(self):
        return [self.level_bytes]

    # Level Data does NOT use default fns
    @staticmethod
    def parse_definition():
        assert False

@parse_wrapper(LevelData)
def level_data_parser(address, obj_names, rom, data):
    room_width, room_height = data
    # Total amount of data is 5 bytes per tile (layer1, BTS, layer2)
    # And there are 256 tiles per screen
    #TODO: the total amount of level data could theoretically exceed this with bad compression
    max_data = 5 * room_width * 16 * room_height * 16
    max_bytes = rom.read_from_clean(address, max_data)
    level_bytes = decompress.decompress(max_bytes)
    return [level_bytes], len(level_bytes)

@compile_wrapper
def level_data_compiler(obj, obj_names, obj_Addrs, obj_bytes, rom, bank):
    compressed_bytes = compress.greedy_compress(obj.level_bytes)
    return compressed_bytes

LevelData.fns = (level_data_parser, level_data_compiler)

class PLMList(RomObject):
    name_def = "PLM_list_{}"

    @auto_init
    def __init__(self, l, name):
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
    name_def = "PLM_{}"

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

PLM.fns = mk_default_fns(PLM)

class Scrolls(RomObject):
    name_def = "scrolls_{}"

    @auto_init
    def __init__(self, array, name):
        pass

    def list(self):
        return [self.array]

    @staticmethod
    def parse_definition():
        assert False

@parse_wrapper(Scrolls)
def scrolls_parser(address, obj_names, rom, data):
    room_width, room_height = data
    n_scrolls = room_width * room_height
    scroll_array = np.zeros(data, dtype=int)
    # Scrolls are stored in column major order
    # If the address was an invalid pointer, scrolls can have a special meaning
    try:
        address = Address(address, mode="snes")
        scroll_bytes = rom.read_from_clean(address, n_scrolls)
    except IndexError:
        # 0x0000 -> All blue
        if address == 0x8f0000:
            scroll_bytes = b"\x01" * n_scrolls
        # 0x0001 -> All green
        elif address == 0x8f0001:
            scroll_bytes = b"\x02" * n_scrolls
        else:
            assert False, "Bad scrolls address: {}".format(hex(address))
    # Iterating through bytestring gives int
    for i, b in enumerate(scroll_bytes):
        x = i % room_width
        y = i // room_width
        if b in list(ScrollValue):
            scroll_array[x][y] = b
        else:
            assert False, "Bad scroll: {}".format(b)
    return [scroll_array], len(scroll_bytes)

@compile_wrapper
def scrolls_compiler(obj, obj_names, obj_Addrs, obj_bytes, rom, bank):
    # If all blue / green, don't need to allocate
    #TODO: Fix in pointer-replacement stage
    if np.all(obj.array == ScrollValue.BlueScroll):
        return b""
    elif np.all(obj.array == ScrollValue.GreenScroll):
        return b""
    # Convert from numpy array to bytes in row major order
    # Use mutable bytearray rather than bytestring
    obj_bytes = bytearray()
    x_dim, y_dim = obj.array.shape
    for x in range(x_dim):
        for y in range(y_dim):
            b = int.to_bytes(obj.array[x][y], 1)
            scroll_bytes.append(b)
    # Convert back to bytestring
    return bytes(scroll_bytes)

Scrolls.fns = (scrolls_parser, scrolls_compiler)

# Parsing
def parse_from_savestations(savestation_addrs, rom):
    obj_names = {}
    for addr in savestation_addrs:
        SaveStation.fns[0](addr, obj_names, rom, None)
    return obj_names

