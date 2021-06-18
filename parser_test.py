from rom_tools import rom_manager

if __name__ == "__main__":
    rom = rom_manager.RomManager("../roms/sm_clean.smc", "../roms/sm_compile.smc")
    obj_names = rom.parse()
    print(obj_names)
