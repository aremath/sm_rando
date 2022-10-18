from functools import reduce, wraps
import inspect
from enum import IntEnum
import numpy as np
from collections.abc import MutableMapping

from . import byte_ops
from .address import *
from .compress import compress
from .compress import decompress
from . import leveldata_utils

#TODO: A way to save the original bytes and decide whether an object has changed...
#TODO: A way to use an ObjNames where some objects already have bytes

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

class FutureBytes(object):

    """
    Object that represents an unknown pointer of a certain size.
    Compilation happens in two steps: allocation and resolution.
    During allocation, objects have real bytes and FutureBytes, making it possible to
    determine the object's size without knowing exactly what those bytes are.
    During resolution, FutureBytes are resolved by looking at the allocated location of the
    underlying object.
    """
    
    def __init__(self, obj, size, banks):
        self.obj = obj
        self.size = size
        self.banks = banks

    def resolve(self):
        assert hasattr(self.obj, "address")
        assert self.obj.address is not None
        # Make sure that the pointer we got actually goes to the banks we expect
        assert self.obj.address.bank in self.banks
        # Handle scrolls separately
        # (Other things are handled by pointer def is_invalid)
        if hasattr(self.obj, "ptr_bytes"):
            return self.obj.ptr_bytes
        else:
            return self.obj.address.as_snes_bytes(self.size)

def byte_size(byte_obj):
    if type(byte_obj) is bytes:
        return len(byte_obj)
    elif type(byte_obj) is FutureBytes:
        return byte_obj.size
    else:
        raise TypeError

def bytes_size(b_list):
    #print("Getting size of: {}".format(b_list))
    s = sum([byte_size(obj) for obj in b_list])
    #print("Size is: {}".format(s))
    return s

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
    MorphBallMissiles = 0xE652
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
        #print("Using {} at {}".format(parser.__name__, address))
        obj, size = parser(address, obj_names, rom, new_data)
        #print("Got: {}, Size: {} using {} at {}\n".format(obj, size, parser.__name__, address))
        objs.append(obj)
        address += Address(size)
        total_size += size
    return objs, total_size

def compile_engine(obj_def, objs, rom):
    # Unzip to list of compilers
    if len(obj_def) == 0:
        compilers = []
    else:
        compilers = list(zip(*obj_def))[1]
    all_bytes = []
    for compiler, obj in zip(compilers, objs):
        b = compiler(obj, rom)
        # Want to get a flat list of bytes / FutureBytes
        if type(b) is list:
            all_bytes.extend(b)
        else:
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

    def list_compiler(obj_list, rom):
        assert isinstance(obj_list, list), type(obj_list)
        all_bytes = []
        for obj in obj_list:
            obj_bytes = compiler(obj, rom)
            if type(obj_bytes) is list:
                all_bytes.extend(obj_bytes)
            else:
                all_bytes.append(obj_bytes)
        if terminal is not None:
            all_bytes.append(terminal)
        return all_bytes

    return list_parser, list_compiler

def pointer_def(constructor, ptr_size, banks, invalid_bytes=None, invalid_ok=False):
    parser, compiler = constructor.fns
    # If you want all banks, do a range!
    assert len(banks) > 0
    if len(banks) > 1:
        bank = None
    else:
        bank = banks[0]

    def pointer_parser(address, obj_names, rom, data):
        address_bytes = rom.read_from_clean(address, ptr_size)
        address_int = int.from_bytes(address_bytes, byteorder="little")
        if invalid_bytes is not None and address_bytes == invalid_bytes:
            return None, ptr_size
        #print(address_bytes)
        #print(hex(address_int))
        # If invalid pointers are ok, call the parser on the raw integer
        # We will trust the parser to handle things properly
        if invalid_ok:
            if bank is None:
                address = address_int
            else:
                address = address_int + (bank << 16)
        elif bank is None:
            assert ptr_size == 3
            address = Address(address_int, mode="snes")
        else:
            assert ptr_size == 2
            address = Address(address_int, mode="snes")
            address = address + Address((bank << 16) + 0x8000, mode="snes")
        #print(hex(address.as_pc))
        name = constructor.name_def.format(address)
        parser(address, obj_names, rom, data)
        return name, ptr_size

    def pointer_compiler(obj, rom):
        if invalid_bytes is not None and obj is None:
            return invalid_bytes
        # Run the compiler for the sub-object, which will result in the
        # object being assigned an address and bytes
        # Compile the sub-object in the requested bank
        obj_bytes = compiler(obj, rom)
        # If an invalid pointer means something, it was treated as an int
        # and translated by the parser
        if invalid_ok:
            # The sub-compiler should do reverse translation and set this field when appropriate
            if hasattr(obj, "ptr_bytes"):
                return obj.ptr_bytes
            # Otherwise, it was actually valid and we can convert to an Address
            else:
                old_address = Address(obj.old_address, mode="snes")
        else:
            old_address = obj.old_address
        # If it's None, then we're still inside the compile for that object
        # in a different iteration -> object will be allocated later
        if obj_bytes is not None:
            # Size of the object on the other end of the pointer
            obj_size = bytes_size(obj.bytes)
            # Register the real value
            # Skip addrs if it's preallocated
            # If the object already has a place on the rom, allocate it there
            #TODO: the new size can be larger as long as it extends into free space
            #TODO: allocation should be the responsibility of pointer_def?
            if old_address is not None and obj_size <= obj.old_size:
                #if obj_size < obj.old_size:
                #    print("Compiled object {} is smaller".format(obj.name))
                assert old_address.bank in banks
                obj.address = old_address
            else:
                #print(banks)
                addr = rom.memory.allocate(obj_size, banks)
                print("Allocating compiled object {} of size {} at {}. Old size: {}".format(obj.name, obj_size, addr, obj.old_size))
                obj.address = addr
        return FutureBytes(obj, ptr_size, banks)

    return pointer_parser, pointer_compiler

# Actual parsers
#def parse_engine(obj_def, address, obj_names, rom):
#def compile_engine(obj_def, obj, rom):

def parse_wrapper(constructor):
    """
    Responsible for all the bookkeeping associated with parsing an object
    The inner function should only return the list of object args (while recursively calling other parsers)
    """
    def inner(func):
        @wraps(func)
        def wrapper(address, obj_names, rom, data):
            # Use the address the object was parsed from to determine the name
            # Parser can theoretically be fooled into parsing multiple different types of object
            # from the same address, and maybe that's OK (that's how the game code works, after all)
            name = constructor.name_def.format(address)
            # Use the address as the name for parsing
            # Already being parsed
            if name in obj_names:
                return
            # Register it first so that it won't be processed twice
            obj_names[name] = None
            #print("Parsing: {}".format(name))
            s_objs, size = func(address, obj_names, rom, data)
            #print(constructor)
            #print(s_objs)
            #print("Done Parsing: {}".format(name))
            # Give the object information about where it came from, and
            # the ability to use obj_names for indexing
            s = constructor(name, address, size, obj_names, *s_objs)
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
    def wrapper(obj, rom):
        # Already being compiled
        if hasattr(obj, "bytes"):
            return
        # Register so that it won't be processed twice.
        #print("Compiling: {}".format(obj.name))
        obj.bytes = None
        obj.bytes = func(obj, rom)
        #print("From {} Got: {}".format(obj.name, obj.bytes))
        return obj.bytes
    return wrapper

def mk_default_fns(constructor, obj_def=None):
    # By default, use the default definition
    if obj_def is None:
        obj_def = constructor.parse_definition

    @parse_wrapper(constructor)
    def parser(address, obj_names, rom, data):
        return parse_engine(obj_def(), address, obj_names, rom, data)

    @compile_wrapper
    def compiler(obj, rom):
        return compile_engine(obj_def(), obj.list, rom)

    return parser, compiler

# Useful for an optional argument
def parse_nothing(address, obj_names, rom, data):
    return None, 0

def compile_nothing(obj, rom):
    return b""

nothing_fns = (parse_nothing, compile_nothing)

def parse_int(address, obj_names, rom, data):
    int_b = rom.read_from_clean(address, 1)
    i = int.from_bytes(int_b, byteorder="little")
    return i, 1

def compile_int(obj, rom):
    int_b = obj.to_bytes(1, byteorder="little")
    return int_b

int_fns = (parse_int, compile_int)

def parse_int2(address, obj_names, rom, data):
    int_b = rom.read_from_clean(address, 2)
    i = int.from_bytes(int_b, byteorder="little")
    return i, 2

def compile_int2(obj, rom):
    int_b = obj.to_bytes(2, byteorder="little")
    return int_b

#TODO: tuple_fns for x, y pairs
int2_fns = (parse_int2, compile_int2)

def parse_condition(address, obj_names, rom, data):
    assert False

def compile_condition(obj, rom):
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
    def enum_compiler(obj, rom):
        # Can simply call the under-parser for an IntEnum
        return under_compiler(obj, rom)
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
    def enum_compiler(obj, rom):
        i = 0
        for b in obj:
            i |= b
        return under_compiler(i, rom)
    return enum_parser, enum_compiler

cre_set_fns = mk_bitset_fns(int_fns, CRESettings)
boss_set_fns = mk_bitset_fns(int_fns, BossSettings)

# This is a function instead of a dictionary because Door hasn't been defined yet
def get_cond_arg_fns(condition):
    if condition == Condition.Default:
        return nothing_fns
    elif condition == Condition.DoorCheck:
        return pointer_def(Door, 2, banks=[0x83]),
    elif condition == Condition.AreaBossDefeated:
        return nothing_fns
    elif condition == Condition.Event:
        return event_fns
    elif condition == Condition.BossDefeated:
        return boss_set_fns
    elif condition == Condition.MorphBall:
        return nothing_fns
    elif condition == Condition.MorphBallMissiles:
        return nothing_fns
    elif condition == Condition.PowerBombs:
        return nothing_fns
    elif condition == Condition.SpeedBooster:
        return nothing_fns
    else:
        assert False, "Bad Condition Type: {}".format(hex(condition))

def parse_state_condition(address, obj_names, rom, data):
    cond, size = parse_condition(address, obj_names, rom, data)
    arg_fns = get_cond_arg_fns(cond)
    arg_parser = arg_fns[0]
    arg_address = address + Address(size)
    arg, arg_size = arg_parser(arg_address, obj_names, rom, data)
    return (cond, arg), (size + arg_size)

def compile_state_condition(obj, rom):
    cond, arg = obj
    cond_bytes = compile_condition(cond, rom)
    arg_fns = get_cond_arg_fns(cond)
    arg_compiler = arg_fns[1]
    arg_bytes = arg_compiler(arg, rom)
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

class ObjNames(MutableMapping):
    """ Glorified dict that keeps track of IDs to
    allow for the creation of new objects with unique names. """

    def __init__(self):
        self.d = {}
        self.new_obj_id = 0

    def __getitem__(self, k):
        return self.d[k]

    def __setitem__(self, k, v):
        self.d[k] = v

    def __iter__(self):
        return self.d.__iter__()
    
    def __len__(self):
        return self.d.__len__()

    def __delitem__(self, k):
        return self.d.__delitem__(k)

    # TODO: delete which auto unallocates from rom.memory
    def create(self, constructor, *args, replace=None, obj_name=None):
        """ Register a new object of the given type by instantiating it
        with *args """
        if obj_name is None:
            obj_name = constructor.name_def.format(self.new_obj_id)
            self.new_obj_id += 1
        # Use replace to allocate the new object on top of an existing object
        if replace is not None:
            old_address = replace.old_address
            old_size = replace.old_size
        else:
            old_address = None
            old_size = None
        obj = constructor(obj_name, old_address, old_size, self, *args)
        # Register the new object
        self[obj_name] = obj
        return obj

    def copy_obj(self, obj, replace=None, new_name=None):
        """
        Move a name from other to self, and also take along all other names it depends on.
        If replace is not None, then some pointers will be replaced before allocation.
        """
        assert obj.obj_names != self, "Copying an object from the same place!"
        assert isinstance(obj, RomObject)
        # We're already done
        if obj.name in self:
            return obj
        constructor = type(obj)
        if new_name is None:
            new_name = obj.name
        # Use object's getattr to avoid the standard pointer dereferencing
        args = [object.__getattribute__(obj, name) for name in obj.fields]
        # Do the replacement (need to use string pointers)
        if replace is not None:
            assert len(replace) == len(args)
            new_args = []
            for o, r in zip(args, replace):
                if r is None:
                    new_args.append(o)
                else:
                    new_args.append(r)
            args = new_args
        new_obj = constructor(new_name, None, None, self, *args)
        self[new_name] = new_obj
        # Now recursively add dependencies
        # Now we WANT the dereferencing
        new_attrs = [new_obj.__getattribute__(name) for name in obj.fields]
        for attr in new_attrs:
            if isinstance(attr, RomObject):
                # Replace and new_name only for the top-level object
                _ = self.copy_obj(attr)
        return new_obj

    # Return the addresses of the RoomHeader objects for use with SMILE RF
    def room_mdb(self):
        # Do not include uncompiled rooms
        rooms = filter(lambda x: type(x) is RoomHeader, self.values())
        rooms2 = filter(lambda x: hasattr(x, "address"), rooms)
        if len(rooms) != len(rooms2):
            print("Warning: obj_names has uncompiled room headers!")
        # Remove 0x and convert hex letters to upper case
        a_strs = [str(r.address).upper()[2:] for r in rooms2]
        return "\n".join(a_strs)

# Classes

class RomObject(object):
    name_def = None
    fields = []

    def __init__(self, name, old_address, old_size, obj_names, *args):
        self.name = name
        self.old_address = old_address
        self.old_size = old_size
        self.obj_names = obj_names
        fields = type(self).fields
        assert len(fields) == len(args), f"Number of arguments ({len(args)}) does not match number of parameters ({len(fields)})"
        for field, arg in zip(fields, args):
            setattr(self, field, arg)

    @property
    def list(self):
        return [getattr(self, field) for field in type(self).fields]
    
    @staticmethod
    def parse_definition():
        assert False

    # Override getattribute to allow implicit indexing
    def __getattribute__(self, name):
        default_attr = object.__getattribute__(self, name)
        # If it's a string, dereference via obj_names
        # Allow self.name as a self-reference that will return a string
        if type(default_attr) is str and self.obj_names[default_attr] is not self:
            return self.obj_names[default_attr]
        if type(default_attr) is list:
            if len(default_attr) == 0:
                return []
            elif type(default_attr[0]) is str:
                return [self.obj_names[i] for i in default_attr]
        # As a fallback, return the requested object
        return default_attr

    def __repr__(self):
        return "{}".format(object.__getattribute__(self, "name"))

# Placeholder class for something we don't know how to parse yet
# Currently parsing asm does nothing - too hard to know which parts of the code are
# relevant + how to repoint. This is certainly an interesting concept though
class Placeholder(RomObject):
    name_def = "placeholder_{}"
    fields = []
    
    @staticmethod
    def parse_definition():
        return []

Placeholder.fns = mk_default_fns(Placeholder)

#TODO: how to force allocation in the pre-defined savestation tables?
class SaveStation(RomObject):
    """
    Save Stations. The roots of the parsing / compilation process.
    """
    name_def = "save_station_{}"
    fields = ["room", "door", "save_x", "save_y", "samus_x", "samus_y"]

    # Definitions
    # These are functions to avoid circular dependency because the parsers are
    # mutually recursive
    # They will by evaluated dynamically
    #TODO: I'm certain there is a better way to do this, but I can't think of what it is
    @staticmethod
    def parse_definition():
        return [
        pointer_def(RoomHeader, 2, banks=[0x8F]),
        pointer_def(Door, 2, banks=[0x83]),
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
    fields = ["room_index", "area_index", "map_x", "map_y", "width", "height", "scroll_up",
                "scroll_down", "CRE_bitset", "door_list", "state_chooser"]

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
        pointer_def(DoorList, 2, banks=[0x8F]), # Door List Pointer
        (*StateChooser.fns, get_room_dims), # State Conditions to decide which RoomState to load
        ]

    def all_states(self):
        return [s.state for s in self.state_chooser.conditions] + [self.state_chooser.default]

RoomHeader.fns = mk_default_fns(RoomHeader)

class StateChoice(RomObject):
    name_def = "state_condition_{}"
    fields = ["state_condition", "state"]

    @staticmethod
    def parse_definition():
        return [
        state_condition_fns,
        (*pointer_def(RoomState, 2, banks=[0x8F]), data_pass),
        ]

StateChoice.fns = mk_default_fns(StateChoice)

#TODO: can we get away without some of these objects that just store lists?
class StateChooser(RomObject):
    name_def = "state_chooser_{}"
    #TODO: merge into one list?
    fields = ["conditions", "default"]

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
    fields = ["level_data", "tileset", "music_data", "music_track", "fx", "enemy_list",
                "enemy_types", "layer2_scroll_x", "layer2_scroll_y", "scrolls",
                "special_xray", "main_asm", "plms", "background_index", "setup_asm"]

    @staticmethod
    def parse_definition():
        return [
        (*pointer_def(LevelData, 3, banks=range(0xc2, 0xcf)), data_pass),# Level Data in banks C2-CE inclusive
        int_fns,                                # Tileset
        int_fns,                                # Music data index
        int_fns,                                # Music track index
        pointer_def(FX, 2, banks=[0x83]),          # FX Data
        pointer_def(EnemyList, 2, banks=[0xA1]),   # The enemies in the room
        pointer_def(EnemyTypes, 2, banks=[0xB4]),  # The enemy types available in the room
        int_fns,                                # Layer 2 scroll X
        int_fns,                                # Layer 2 scroll Y
        (*pointer_def(Scrolls, 2, banks=[0x8F], invalid_ok=True), data_pass), # Scrolls
        pointer_def(Placeholder, 2, banks=[0x8F], invalid_bytes=b"\x00\x00"), # Special x-ray blocks
        #TODO: 8F is just a guess
        pointer_def(Placeholder, 2, banks=[0x8F], invalid_bytes=b"\x00\x00"), # Main ASM
        pointer_def(PLMList, 2, banks=[0x8F]),     # PLMs
        #TODO: 8F is just a guess
        pointer_def(Placeholder, 2, banks=[0x8F], invalid_bytes=b"\x00\x00"),  # Library background for Layer 2 data
        #TODO: 8F is just a guess
        pointer_def(Placeholder, 2, banks=[0x8F], invalid_bytes=b"\x00\x00"), # Setup ASM
        ]

RoomState.fns = mk_default_fns(RoomState)

class Door(RomObject):
    name_def = "door_{}"
    #TODO: instead of low / high, is this door cap position and screen position?
    fields = ["to_room", "elevator_properties", "orientation",
                "x_pos_low", "y_pos_low", "x_pos_high", "y_pos_high",
                "spawn_distance", "asm_pointer"]

    @staticmethod
    def parse_definition():
        return [
        pointer_def(RoomHeader, 2, banks=[0x8F]),
        #TODO special parsers for elevator + orientation
        int_fns,   # Elevator properties
        int_fns,   # Orientation
        int_fns,   # X position low byte
        int_fns,   # Y position low byte
        int_fns,   # X position high byte
        int_fns,   # Y position high byte
        int2_fns, # Distance from door to spawn Samus
        pointer_def(Placeholder, 2, banks=[0x8F], invalid_bytes=b"\x00\x00"),   # Door ASM
        ]

# Special case: Door of \x00\x00 is used for elevators
@parse_wrapper(Door)
def door_parser(address, obj_names, rom, data):
    if rom.read_from_clean(address, 2) == b"\x00\x00":
        return [None] * 9, 2
    else:
        return parse_engine(Door.parse_definition(), address, obj_names, rom, data)

#TODO: can combine these pointers!
@compile_wrapper
def door_compiler(obj, rom):
    # Only need to check the to_room, since you can't normally have a blank to_room.
    if obj.to_room is None:
        return [b"\x00\x00"]
    else:
        return compile_engine(Door.parse_definition(), obj.list, rom)

Door.fns = (door_parser, door_compiler)

# A door list doesn't have a terminal
# Instead, it's over when we run out of valid addresses
def door_list_check(address, rom):
    b = rom.read_from_clean(address, 2)
    i = int.from_bytes(b, byteorder="little")
    return byte_ops.valid_snes(i)

#TODO: Elevators
class DoorList(RomObject):
    name_def = "door_list_{}"
    fields = ["l"]

    @staticmethod
    def parse_definition():
        return [
        list_def(pointer_def(Door, 2, banks=[0x83]), None, door_list_check)
        ]

DoorList.fns = mk_default_fns(DoorList)

class FXEntry(RomObject):
    name_def = "fx_entry_{}"
    fields = ["door", "liquid_y", "liquid_target_y", "liquid_speed", "liquid_timer",
                "layer3_type", "default_layer_blend", "layer3_blend", "liquid_options",
                "palette_fx_bits", "animated_tiles_bits", "palette_blend"]

    @staticmethod
    def parse_definition():
        return [
        pointer_def(Door, 2, banks=[0x83]),
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
    fields = ["fx_l", "default_fx"]

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
def fx_compiler(obj, rom):
    if len(obj.fx_l) == 0 and obj.default_fx is None:
        return [b"\xff\xff"]
    else:
        return compile_engine(FX.parse_definition(), obj.list, rom)

FX.fns = (fx_parser, fx_compiler)

class EnemyList(RomObject):
    name_def = "enemy_list_{}"
    # kill_count: Number of enemy deaths needed to clear the current room
    fields = ["enemies", "kill_count"]

    @staticmethod
    def parse_definition():
        return [
        list_def(Enemy.fns, b"\xff\xff"), # Enemies in the room
        int_fns # Number of enemy deaths needed to clear the room (used for grey doors?)
        ]

EnemyList.fns = mk_default_fns(EnemyList)

class Enemy(RomObject):
    name_def = "enemy_{}"
    fields = ["enemy_id", "x_pos", "y_pos", "init_param", "properties1", "properties2",
                "parameter1", "parameter2"]

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

#TODO: complain during compilation if more than four types are present
class EnemyTypes(RomObject):
    name_def = "enemy_types_{}"
    fields = ["l"]

    @staticmethod
    def parse_definition():
        return [
        list_def(EnemyType.fns, b"\xff\xff")
        ]

EnemyTypes.fns = mk_default_fns(EnemyTypes)

class EnemyType(RomObject):
    name_def = "enemy_type_{}"
    fields = ["enemy_id", "palette_index"]

    @staticmethod
    def parse_definition():
        return [
        int2_fns, # Enemy ID #TODO: really is a pointer
        int2_fns, # Palette Index
        ]

EnemyType.fns = mk_default_fns(EnemyType)

class LevelData(RomObject):
    name_def = "level_data_{}"
    # Storing as an array as well as in custom data structure with fields
    fields = ["level_bytes", "level_array", "compressed_data"]

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
    # Return the size of the COMPRESSED data (for allocation purposes)
    # The new room could fit at the location where it originally existed
    #print(address)
    level_bytes, size = decompress.decompress_with_size(max_bytes)
    compressed_data = rom.read_from_clean(address, size)
    level_dimensions = leveldata_utils.Coord(room_width * 16, room_height * 16)
    level_array = leveldata_utils.level_array_from_bytes(level_bytes, level_dimensions)
    return [level_bytes, level_array, compressed_data], size

@compile_wrapper
def level_data_compiler(obj, rom):
    # If the object was parsed, we already know the compressed data
    # Can set this field to None in order to force recompression on compile
    if obj.compressed_data is not None:
        return [obj.compressed_data]
    else:
        compressed_bytes = compress.greedy_compress(obj.level_bytes)
        return [compressed_bytes]

LevelData.fns = (level_data_parser, level_data_compiler)

class PLMList(RomObject):
    name_def = "PLM_list_{}"
    fields = ["l"]

    @staticmethod
    def parse_definition():
        return [
            list_def(PLM.fns, b"\x00\x00")
        ]

PLMList.fns = mk_default_fns(PLMList)

class PLM(RomObject):
    name_def = "PLM_{}"
    fields = ["plm_id", "x_pos", "y_pos", "parameter"]

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
    fields = ["array"]

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
        # An invalid scroll pointer has special behavior
        # The bottom row of scrolls is set to the low byte + 1
        # The rest of the scrolls are green
        low_byte = address & 0xff
        greens = b"\x02" * room_width * (room_height - 1)
        others = int.to_bytes(low_byte + 1, 1, byteorder="little") * room_width
        scroll_bytes = greens + others
        assert len(scroll_bytes) == n_scrolls
    # Iterating through bytestring gives int
    for i, b in enumerate(scroll_bytes):
        x = i % room_width
        y = i // room_width
        if b in list(ScrollValue):
            scroll_array[x][y] = b
        # Things that are not 00 or 01 (Red or Blue) are treated as green
        # We will change the data here to be more consistent
        else:
            scroll_array[x][y] = ScrollValue.GreenScroll
    return [scroll_array], len(scroll_bytes)

@compile_wrapper
def scrolls_compiler(obj, rom):
    # If all blue / green, don't need to allocate
    #TODO: Fix in pointer-replacement stage
    bot_value = obj.array[-1][0]
    bot_row = obj.array[-1:]
    non_bot_row = obj.array[:-1]
    if np.all(bot_row == bot_value) and np.all(non_bot_row == ScrollValue.GreenScroll):
        # Negative values wrap around
        ptr_val = (int(bot_value) - 1) % 256
        # Little endian, so \x00 goes later
        obj.ptr_bytes = int.to_bytes(ptr_val, 1, byteorder="little") + b"\x00"
        return b""
    # Convert from numpy array to bytes in row major order
    # Use mutable bytearray rather than bytestring
    scroll_bytes = bytearray()
    x_dim, y_dim = obj.array.shape
    for y in range(y_dim):
        for x in range(x_dim):
            # Convert from numpy int64 to python int
            b = int.to_bytes(int(obj.array[x][y]), 1, byteorder="little")
            scroll_bytes.extend(b)
    # Convert back to bytestring
    return [bytes(scroll_bytes)]

Scrolls.fns = (scrolls_parser, scrolls_compiler)

# Parsing
def parse_from_savestations(savestation_addrs, rom):
    obj_names = ObjNames()
    for addr in savestation_addrs:
        SaveStation.fns[0](addr, obj_names, rom, None)
    return obj_names

# Compiling
def compile_from_savestations(savestation_objs, obj_names, rom):
    # Allocation
    print("ALLOCATION")
    # Adds "address" and "bytes" fields to each object
    #TODO: Use a dictionary from bank -> bytes -> address (hash FutureAddress by name, size)
    # to avoid repetition (each compiler can check before allocation)
    for obj in savestation_objs:
        # Do not allow Save Stations to be allocated outside of their normal location
        # Levels built from scratch should include old_address for savesation objects
        # and for other preallocated objects like default setup ASM
        #print("Starting {}".format(obj.name))
        SaveStation.fns[1](obj, rom)
        obj.address = obj.old_address
        #print("Done with {}".format(obj.name))
    print("POINTER RESOLUTION")
    # Pointer resolution
    for name, obj in obj_names.items():
        # Use mutable bytearray for speed
        obj_bytes = bytearray()
        #print(name)
        #print(obj.name)
        #print(obj.bytes)
        # Objects no longer pointed to are not compiled
        if hasattr(obj, "bytes"):
            for i,b in enumerate(obj.bytes):
                if type(b) is bytes:
                    obj_bytes += b
                elif type(b) is FutureBytes:
                    obj_bytes += b.resolve()
                else:
                    raise TypeError
            # Set it
            obj.true_bytes = bytes(obj_bytes)
    print("WRITING")
    # Write bytes out
    for obj in obj_names.values():
        if hasattr(obj, "address"):
            rom.write_to_new(obj.address, obj.true_bytes)

