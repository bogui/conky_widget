-- Calendar + weather widget. One file for every monitor: head from CONKY_HEAD.
local head = tonumber(os.getenv("CONKY_HEAD") or "0") or 0

conky.config = {
    alignment = 'top_left',
    xinerama_head = head,
    gap_x = 400,              -- to the right of the system widget (25 + 330 + margin)
    gap_y = 40,               -- just below the 32 px GNOME top bar
    minimum_width = 270,
    minimum_height = 5,

    own_window = true,
    own_window_class = 'Conky',
    own_window_type = 'desktop',
    own_window_transparent = true,
    own_window_argb_visual = true,
    own_window_argb_value = 180,
    own_window_hints = 'undecorated,sticky,below,skip_taskbar,skip_pager',
    double_buffer = true,
    background = false,
    out_to_x = true,
    out_to_wayland = false,
    out_to_console = false,

    use_xft = true,
    font = 'Liberation Sans:size=10',
    default_color = '#E0E0E0',
    draw_borders = false,
    draw_graph_borders = false,
    draw_outline = false,
    draw_shades = false,
    border_width = 0,
    stippled_borders = 0,
    extra_newline = false,
    uppercase = false,
    use_spacer = 'none',

    update_interval = 1.0,    -- the clock shows seconds
    no_buffers = true,
}

conky.text = [[
${color #FFFFFF}${font Liberation Sans:bold:size=14}КАЛЕНДАР${font}${color}
${hr 2}
${color #B0B0B0}Дата:${color #FFFFFF} ${execpi 60 ~/.local/bin/date_bg.py date}
${color #B0B0B0}Час:${color #FFFFFF} ${time %H:%M:%S}
${color #B0B0B0}Седмица:${color #FFFFFF} ${execpi 600 ~/.local/bin/date_bg.py week}

${color #FFFFFF}${font Liberation Sans:bold:size=14}Прогноза за Русе${font}${color}
${hr 2}
${color #B0B0B0}Сега:${color} ${execpi 600 ~/.local/bin/weather_ruse.py current}
${execpi 600 ~/.local/bin/weather_ruse.py details}
${color #B0B0B0}Следващите часове:${color}
${execpi 600 ~/.local/bin/weather_ruse.py today}
${color #B0B0B0}Следващите дни:${color}
${execpi 600 ~/.local/bin/weather_ruse.py week}
]]
