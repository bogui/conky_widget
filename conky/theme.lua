-- Shared colour helpers for the conky widget.
-- Loaded via lua_load; functions are called as ${lua conky_<name> ...}.

local BLUE, GREEN, ORANGE, RED = "#3961e4", "#34a853", "#fb9905", "#ea4335"

local function color(hex)
    return conky_parse("${color " .. hex .. "}")
end

-- Resolve either a number ("42", "42%") or a conky variable ("cpu", "fs_free_perc /")
local function to_number(...)
    local text = table.concat({...}, " ")
    if text == "" then return nil end
    local n = tonumber((text:gsub("%%", ""):gsub("°C", ""):gsub("%s+", "")))
    if n then return n end
    local parsed = conky_parse("${" .. text:gsub("^%${", ""):gsub("}$", "") .. "}")
    return tonumber((tostring(parsed):gsub("%%", ""):gsub("°C", ""):gsub("%s+", "")))
end

-- Usage percentage -> colour: <25 blue, <50 green, <75 orange, else red
function conky_bar_color(...)
    local pct = to_number(...)
    if not pct then return color(BLUE) end
    if pct < 25 then return color(BLUE)
    elseif pct < 50 then return color(GREEN)
    elseif pct < 75 then return color(ORANGE)
    else return color(RED) end
end

-- Free percentage (fs_free_perc) -> colour of the used share
function conky_disk_bar_color(...)
    local free = to_number(...)
    if not free then return color(BLUE) end
    return conky_bar_color(tostring(100 - free))
end

-- Temperature in °C -> colour: <40 blue, <60 green, <75 orange, else red
function conky_temp_bar_color(...)
    local t = to_number(...)
    if not t then return color(BLUE) end
    if t < 40 then return color(BLUE)
    elseif t < 60 then return color(GREEN)
    elseif t < 75 then return color(ORANGE)
    else return color(RED) end
end
