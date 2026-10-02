
-- Debug function that parses a Conky variable name
function conky_debug_var(varname)
    if varname == nil then
        return "[VARNAME_NIL]"
    end
    local var_str = tostring(varname)
    local parsed = conky_parse("${" .. var_str .. "}")
    if parsed == nil then
        return "[PARSE_FAILED:" .. var_str .. "]"
    end
    return var_str .. "=" .. tostring(parsed)
end

-- Debug function that gets CPU directly
function conky_debug_cpu()
    local cpu_val = conky_parse("${cpu}")
    if cpu_val == nil then
        return "[CPU_NIL]"
    end
    return "CPU=" .. tostring(cpu_val) .. " [" .. type(cpu_val) .. "]"
end

-- Debug function to show the raw value being passed
function conky_debug_value(value)
    if value == nil then
        return "[NIL]"
    end
    local val_str = tostring(value)
    local val_type = type(value)
    return val_str .. " [" .. val_type .. "]"
end

function conky_test()
    return "LUA_WORKS"
end

-- Lua function to get color based on usage percentage
-- Returns color codes: Blue (0-25%), Green (25-50%), Orange (50-75%), Red (75-100%)
-- Accepts either a numeric value or a Conky variable name (e.g., "cpu", "memperc")
function conky_bar_color(percentage)
    if percentage == nil then
        return conky_parse("${color #3961e4}")  -- Default to blue if nil
    end

    local value_str = tostring(percentage)
    local pct = nil

    -- Check if it's a variable name (like "cpu" or "${cpu}") or already a number
    -- First try to parse it as a number directly
    local clean = value_str:gsub("%%", ""):gsub("%s+", "")
    pct = tonumber(clean)

    -- If not a number, try to parse it as a Conky variable
    if pct == nil then
        -- Remove ${} if present
        local var_name = value_str:gsub("${", ""):gsub("}", ""):gsub("%s+", "")
        -- Try to parse the variable
        local parsed = conky_parse("${" .. var_name .. "}")
        if parsed ~= nil then
            clean = tostring(parsed):gsub("%%", ""):gsub("%s+", "")
            pct = tonumber(clean)
        end
    end

    -- If still nil, default to blue
    if pct == nil or pct < 0 then
        return conky_parse("${color #3961e4}")  -- Default to blue for invalid values
    end

    if pct > 100 then
        pct = 100  -- Cap at 100%
    end

        -- Add shading to the colors based on usage percentage.
        -- As pct increases, we'll add "shades" by changing alpha (using rgba) or using slightly different shades.
        -- For Conky, only the hex format is supported, so we'll pick lighter and darker variants.

        -- Blue shades: #3961e4 (base), #547bf2 (lighter), #223374 (darker)
        -- Green shades: #34a853 (base), #6ed97c (lighter), #217a38 (darker)
        -- Orange shades: #fb9905 (base), #ffbc49 (lighter), #b06c00 (darker)
        -- Red shades: #ea4335 (base), #ff7c6b (lighter), #a12a1b (darker)

        -- We'll apply these shades based on the exact value of pct - e.g.:
        -- 0-7: lightest, 8-15: base, 16-25: darkest (adjust per range size)
        if pct <= 7 then
            return conky_parse("${color #547bf2}") -- lighter blue
        elseif pct <= 15 then
            return conky_parse("${color #3961e4}") -- base blue
        elseif pct <= 25 then
            return conky_parse("${color #223374}") -- darker blue

        elseif pct <= 30 then
            return conky_parse("${color #6ed97c}") -- lighter green
        elseif pct <= 45 then
            return conky_parse("${color #34a853}") -- base green
        elseif pct <= 50 then
            return conky_parse("${color #217a38}") -- darker green

        elseif pct <= 60 then
            return conky_parse("${color #ffbc49}") -- lighter orange
        elseif pct <= 75 then
            return conky_parse("${color #fb9905}") -- base orange
        elseif pct <= 85 then
            return conky_parse("${color #b06c00}") -- darker orange

        elseif pct <= 90 then
            return conky_parse("${color #ff7c6b}") -- lighter red
        elseif pct <= 100 then
            return conky_parse("${color #ea4335}") -- base red
        else
            return conky_parse("${color #a12a1b}") -- darker red
        end
        return conky_parse("${color #3961e4}")  -- Blue

end

-- Lua function to get color for disk usage (converts free percentage to used percentage)
-- Accepts either a numeric value or a Conky variable name (e.g., "fs_free_perc /")
function conky_disk_bar_color(free_perc)
    if free_perc == nil then
        return conky_parse("${color #3961e4}")  -- Default to blue if nil
    end

    local value_str = tostring(free_perc)
    local free = nil

    -- Check if it's a variable name or already a number
    local clean = value_str:gsub("%%", ""):gsub("%s+", "")
    free = tonumber(clean)

    -- If not a number, try to parse it as a Conky variable
    if free == nil then
        -- For disk variables like "fs_free_perc /", we need to handle the space
        local var_name = value_str:gsub("${", ""):gsub("}", ""):gsub("^%s+", ""):gsub("%s+$", "")
        -- Try to parse the variable
        local parsed = conky_parse("${" .. var_name .. "}")
        if parsed ~= nil then
            clean = tostring(parsed):gsub("%%", ""):gsub("%s+", "")
            free = tonumber(clean)
        end
    end

    if free == nil or free < 0 then
        free = 100  -- Default to 100% free (0% used) for invalid values
    end
    if free > 100 then
        free = 100
    end
    local used = 100 - free
    -- Pass as number to conky_bar_color
    return conky_bar_color(tostring(used))
end

-- Lua function to get color for temperature (converts temperature to percentage and uses bar_color)
-- Accepts multiple arguments that form the hwmon variable (e.g., "hwmon", "0", "temp", "1")
-- or a single numeric value
-- Assumes max temperature of 90°C (100% usage) for color calculation
function conky_temp_bar_color(...)
    local args = {...}
    if #args == 0 or args[1] == nil then
        return conky_parse("${color #3961e4}")  -- Default to blue if nil
    end

    local temp = nil

    -- If only one argument and it's a number, use it directly
    if #args == 1 then
        local value_str = tostring(args[1])
        local clean = value_str:gsub("%°C", ""):gsub("°C", ""):gsub("%%", ""):gsub("%s+", "")
        temp = tonumber(clean)

        -- If not a number, try to parse as a variable (for backward compatibility)
        if temp == nil then
            local var_name = value_str:gsub("${", ""):gsub("}", ""):gsub("^%s+", ""):gsub("%s+$", "")
            local parsed = conky_parse("${" .. var_name .. "}")
            if parsed ~= nil then
                clean = tostring(parsed):gsub("%°C", ""):gsub("°C", ""):gsub("%%", ""):gsub("%s+", "")
                temp = tonumber(clean)
            end
        end
    else
        -- Multiple arguments: reconstruct the hwmon variable name
        -- e.g., "hwmon", "0", "temp", "1" -> "hwmon 0 temp 1"
        local var_name = table.concat(args, " ")
        local parsed = conky_parse("${" .. var_name .. "}")
        if parsed ~= nil then
            local clean = tostring(parsed):gsub("%°C", ""):gsub("°C", ""):gsub("%%", ""):gsub("%s+", "")
            temp = tonumber(clean)
        end
    end

    if temp == nil or temp < 0 then
        return conky_parse("${color #3961e4}")  -- Default to blue for invalid values
    end

    -- Use temperature-specific thresholds (not percentage-based)
    -- < 40°C = Blue (cool/good), 40-60°C = Green (normal/good), 60-75°C = Orange (warm/acceptable), > 75°C = Red (hot/warning)
    if temp < 40 then
        return conky_parse("${color #3961e4}")  -- Blue
    elseif temp < 60 then
        return conky_parse("${color #34a853}")  -- Green
    elseif temp < 75 then
        return conky_parse("${color #fbbc05}")  -- Orange
    else
        return conky_parse("${color #ea4335}")  -- Red
    end
end
