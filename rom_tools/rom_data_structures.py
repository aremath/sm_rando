from functools import reduce
import os
from . import byte_ops
from .address import *
from .compress import compress

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
       
        # Data members that will be allocated then become pointers
        sym_ptr = "room_{}_".format(room_id)
        self.sym_ptr = sym_ptr
        # Future pointer to the room header that holds this state
        self.room_head = FutureAddress(sym_ptr + "head")
        # This is a future pointer to where the event's state will be within the room header
        self.state_ptr = get_future_ptr(state_id, "state", sym_ptr)
        self.level_data_ptr = get_future_ptr(level, "level", sym_ptr)
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
        self.background_ptr = get_future_ptr(background, "background", sym_ptr)
        self.setup_asm_ptr = get_future_ptr(setup_asm, "setup_asm", sym_ptr)

    def to_bytes(self, pos):
        futures = []
        if self.default_event == True:
            head = self.event_head
        # The extra two bytes will be used to store a pointer to the rest of the event data
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
# (for a door to be a symbolic pointer string instead of a Door)
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

        # Important (future) pointers
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
        # Write at the end of the header a future pointer to where the doors are placed
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
        to_write = get_compressed(self)
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

#TODO - doors should be able to allocate their own asm if necessary
class Door(object):

    def __init__(self, door_id, from_room_id, to_room_id, bitflag, direction,
            door_cap_xy, screen_xy, spawn_distance, asm_ptr):
        self.from_sym = "room_{}_door_{}".format(from_room_id, door_id)
        self.from_sym_ptr = FutureAddress(self.from_sym) 
        self.to_sym = "room_{}_head".format(to_room_id)
        self.to_sym_ptr = FutureAddress(self.to_sym)
        self.bitflag = bitflag.to_bytes(1, byteorder='little')
        self.direction = direction_convert(direction[0], direction[1]).to_bytes(1, byteorder='little')
        self.door_cap_x = door_cap_xy[0].to_bytes(1, byteorder='little')
        self.door_cap_y = door_cap_xy[1].to_bytes(1, byteorder='little')
        self.screen_x = screen_xy[0].to_bytes(1, byteorder='little')
        self.screen_y = screen_xy[1].to_bytes(1, byteorder='little')
        self.spawn_distance = spawn_distance.to_bytes(2, byteorder='little')
        self.asm_ptr = asm_ptr.to_bytes(2, byteorder='little')

    def to_bytes(self):
        futures = []
        out = b""
        out += b"\x00\x00"
        futures.append(FutureAddressWrite(self.to_sym_ptr, self.from_sym_ptr, 2, bank=0x8f))
        out += self.bitflag
        out += self.direction
        out += self.door_cap_x
        out += self.door_cap_y
        out += self.screen_x
        out += self.screen_y
        out += self.spawn_distance
        out += self.asm_ptr
        assert len(out) == 12
        return out, futures

    def allocate(self, memory, env):
        to_write, fs = self.to_bytes()
        addr = memory.allocate_and_write(to_write, [0x83])
        env[self.from_sym] = addr
        return fs

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

