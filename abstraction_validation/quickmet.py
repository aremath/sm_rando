import retro
import numpy as np

from rom_tools import rom_manager
# make_starting_items doesn't work, because quickmet doesn't read from the required locations.
#TODO: make a function like this that takes an itemset, etc.
from rom_tools.rom_edit import make_starting_items, beam_codes, item_codes
from rom_tools.address import Address
from pathlib import Path

#room_id = 0x92fd
room_id = 0xac5a
#samus_x = 0x0070
#samus_y = 0x0078
samus_x = 0x00100
samus_y = 0x0080
room_id_address = Address(0x59ad0)
samus_x_address = Address(0x59a8a)
samus_y_address = Address(0x59a90)
# Destination room tile, to make the camera work properly
dx_address = Address(0x59ad6)
dy_address = Address(0x59ad7)

def to_bytes(i):
    return i.to_bytes(2, byteorder="little")
        
ammo_locs = {"E": (0x09c2, 0x09c4), "M": (0x09c6, 0x09c8), "S": (0x09ca, 0x09cc), "PB": (0x09cd, 0x09d0)}
ammo_amounts = {"E": 100, "M": 5, "S": 5, "PB": 5}

# Regions (in order): Crateria, Brinstar, Norfair, Wrecked_Ship, Maridia, Tourian, Ceres, Debug
# Boss_ID -> (Region, Bitmask)
boss_info = {"Kraid": 0}

def ram_write(state, address, data):
    np.frombuffer(state, dtype='<u2', count=1, offset=address)[0] = data
        
def make_beams_int(item_set, is_equipped=False):
    bitmask = 0
    for i in item_set:
        if i in beam_codes:
            bitmask += beam_codes[i]
    # De-equip spazer if plasma beam is equipped. Firing while spazer and plasma are both equipped will crash the game
    if is_equipped and "PLB" in item_set and "Spazer" in item_set:
        bitmask -= beam_codes["Spazer"]
    return bitmask

def make_items_int(item_set):
    bitmask = 0
    for i in item_set:
        if i in item_codes:
            bitmask += item_codes[i]
    return bitmask
        
# Goes from SamusState plus additional info to an actual game state.
# Won't preserve stuff like pose, unfortunately.
# Deletes emulator instance since only one at a time is possible.
# Extra_items is of the form {i_type: amount}
def reify_state(rom_path, temp_rom_path, samus_state, room_id, room_offset, is_local, extra_items={"E": 99}):
    # Update the ammo amounts based on the item set
    for ammo_item in ammo_locs.keys():
        if ammo_item in samus_state.items:
            if ammo_item not in extra_items:
                extra_items[ammo_item] = ammo_amounts[ammo_item]
            else:
                extra_items[ammo_item] += ammo_amounts[ammo_item]
    # Set up the quickmet ROM
    rom = rom_manager.RomManager(rom_path, temp_rom_path, mod=False)
    print(__file__)
    print(Path(__file__).parent.parent)
    quickmet_path = Path(__file__).parent.parent / "patches" / "sm_quickmet.ips"
    rom.apply_ips(quickmet_path)
    if is_local:
        p = samus_state.position
    else:
        # Compute the local offset
        p = samus_state.position - room_offset
    samus_x = p.x * 0x10
    samus_y = (p.y + 1) * 0x10 # +1 because the samus Y here is the center, but abstract samus Y is the top.
    print(samus_x, samus_y)
    rom.write_to_new(room_id_address, to_bytes(room_id))
    rom.write_to_new(samus_x_address, to_bytes(samus_x))
    rom.write_to_new(samus_y_address, to_bytes(samus_y))
    rom.write_to_new(dx_address, (samus_x // 0x100).to_bytes(1, byteorder="little"))
    rom.write_to_new(dy_address, (samus_y // 0x100).to_bytes(1, byteorder="little"))
    # Set up the emulation
    emu = retro.RetroEmulator(temp_rom_path)
    gamedata = retro.data.GameData()
    emu.configure_data(gamedata)
    # Wait for the ROM to write values from SRAM
    for i in range(256):
        emu.step()
    state = bytearray(emu.get_state())
    # Set up RAM data (Samus Items, Energy, Missiles, etc.)
    mem_offset = emu.get_state().index(gamedata.memory.blocks[0x7E0000])
    # Write ammo amounts
    for item_type, amount in extra_items.items():
        current_addr, max_addr = ammo_locs[item_type]
        for address in [current_addr, max_addr]:
            ram_write(state, mem_offset + address, amount)
    # Write item bitset
    # 0x9a2 and 0x9a4 equipped / collected
    item_bitmask = make_items_int(samus_state.items)
    ram_write(state, mem_offset + 0x09a2, item_bitmask)
    ram_write(state, mem_offset + 0x09a4, item_bitmask)
    # Write beam bitset
    # 0x9a6 and 0x9a8 (make sure to exclusify plasma / spazer)
    beams_equipped = make_beams_int(samus_state.items, is_equipped=True)
    beams_collected = make_beams_int(samus_state.items)
    ram_write(state, mem_offset + 0x09a6, beams_equipped)
    ram_write(state, mem_offset + 0x09a8, beams_collected)
    # Write bosses
    # 0xd820 for event set
    # 0x7ed828 + (region_id) for bosses
    # 0x7ed828 - 0x7ed82f is 7 single bytes (one per region)
    # Wait for gameplay to start
    hacked_state = bytes(state)
    emu.set_state(hacked_state)
    for i in range(156):
        emu.step()
    # Return the state
    end_state = emu.get_state()
    end_screen = emu.get_screen()
    del emu
    return end_state, end_screen
