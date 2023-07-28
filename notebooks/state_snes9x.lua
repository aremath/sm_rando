f = io.open("ram_snes9x.bin", "wb")
f:write("hello")
f:flush()

local is_normal_gameplay = false

local ram_values = {
    game_state_ptr = 0x0998,
}

local gamestate = 0

local function write_file()
    local memory_values
    if is_normal_gameplay then
        -- TODO: 0x2000?
        memory_values = memory.readbyterange(0, 0x2000)
        memory_values2 = memory.readbyterange(0x7ed7c0, 0x65b)
        -- Overwrite the file
        f:seek("set", 0)
        for _, value in ipairs(memory_values) do
            f:write(string.char(value))
        end
        -- Add the boss info in a separate part of the file (otherwise we'd have to copy a lot of useless ram)
        for _, value in ipairs(memory_values2) do
            f:write(string.char(value))
        end
    end
end

local function use_bridge()
    bridge_fn = loadfile("snes9x_bridge.lua")
    if (bridge_fn ~= nil) then
        bridge_fn()
    end
end

local function display_info()
    gamestate = memory.readword(ram_values.game_state_ptr)
    gui.text(0, 10, tostring(gamestate), 0xffffffff)
    if gamestate == 8 then
        is_normal_gameplay = true
    else
        is_normal_gameplay = false
    end

    if is_normal_gameplay then
        gui.text(0, 0, "Normal Gameplay", 0xffffffff)
        write_file()
        use_bridge()
    else
        gui.text(0, 0, "Not Normal Gameplay", 0xffffffff)
    end
end

memory_values = memory.readbyterange(0, 0x2000)
-- Overwrite the file
f:write(tostring(gamestate))
f:flush()

emu.registerbefore(display_info)
