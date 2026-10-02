-- System widget. One file for every monitor: the head comes from CONKY_HEAD (0, 1, ...).
local head = tonumber(os.getenv("CONKY_HEAD") or "0") or 0
local home = os.getenv("HOME")

conky.config = {
    alignment = 'top_left',
    xinerama_head = head,
    gap_x = 25,
    gap_y = 40,               -- just below the 32 px GNOME top bar
    minimum_width = 330,
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
    show_graph_range = false,
    show_graph_scale = false,
    extra_newline = false,
    uppercase = false,
    use_spacer = 'none',

    update_interval = 2.0,
    cpu_avg_samples = 2,
    net_avg_samples = 2,
    no_buffers = true,

    lua_load = home .. '/.config/conky/theme.lua',
}

conky.text = [[
${color #FFFFFF}${font Liberation Sans:bold:size=14}SYSTEM INFO${font}${color}
${hr 2}
${color #B0B0B0}Hostname:${color #FFFFFF} $nodename
${color #B0B0B0}Kernel:${color #FFFFFF} $kernel
${color #B0B0B0}Uptime:${color #FFFFFF} $uptime_short
${color #B0B0B0}Load Avg:${color #FFFFFF} $loadavg

${color #FFFFFF}${font Liberation Sans:bold:size=14}GMAIL${font}${color}
${hr 2}
${color #B0B0B0}Unread:${color #FFFFFF} ${execpi 60 ~/.local/bin/gmail_render.py count} ${color #B0B0B0}emails
${color #B0B0B0}Recent unread:${color}
${execpi 60 ~/.local/bin/gmail_render.py list 4}

${color #FFFFFF}${font Liberation Sans:bold:size=14}CPU${font}${color}
${hr 2}
${color #B0B0B0}Usage:${lua conky_bar_color cpu} ${cpu}% ${cpubar 8,250}
${color #B0B0B0}Frequency:${color #FFFFFF} ${freq_g} GHz
${color #B0B0B0}Temperature:${lua conky_temp_bar_color hwmon coretemp temp 1} ${hwmon coretemp temp 1}°C
${color #B0B0B0}Top Process:${color #FFFFFF} ${top name 1} ${alignr}${top cpu 1}%

${color #FFFFFF}${font Liberation Sans:bold:size=14}GPU${font}${color}
${hr 2}
${color #B0B0B0}Model:${color #FFFFFF} ${execi 3600 ~/.local/bin/gpu_info.sh name}
${color #B0B0B0}Temperature:${lua conky_temp_bar_color hwmon nouveau temp 1} ${hwmon nouveau temp 1}°C ${alignr}${color #B0B0B0}Power:${color #FFFFFF} ${execi 10 ~/.local/bin/gpu_info.sh power}
${color #B0B0B0}Fan:${color #FFFFFF} ${execi 10 ~/.local/bin/gpu_info.sh fan}

${color #FFFFFF}${font Liberation Sans:bold:size=14}MEMORY${font}${color}
${hr 2}
${color #B0B0B0}RAM:${color #FFFFFF} ${mem} / ${memmax} ${alignr}${memperc}%
${lua conky_bar_color memperc}${membar 8,320}
${color #B0B0B0}Swap:${color #FFFFFF} ${swap} / ${swapmax} ${alignr}${swapperc}%
${lua conky_bar_color swapperc}${swapbar 8,320}
${color #B0B0B0}Top Process:${color #FFFFFF} ${top_mem name 1} ${alignr}${top_mem mem 1}%

${color #FFFFFF}${font Liberation Sans:bold:size=14}DISK${font}${color}
${hr 2}
${color #B0B0B0}Root (/):${color #FFFFFF} ${fs_used /} / ${fs_size /} ${alignr}${fs_free_perc /}% free
${lua conky_disk_bar_color fs_free_perc /}${fs_bar 8,320 /}
${color #B0B0B0}Read:${color #FFFFFF} ${diskio_read} ${alignr}${color #B0B0B0}Write:${color #FFFFFF} ${diskio_write}

${color #FFFFFF}${font Liberation Sans:bold:size=14}NETWORK${font}${color}
${hr 2}
${color #B0B0B0}Public IP:${color #FFFFFF} ${execpi 600 ~/.local/bin/get_public_ip.sh}
${color #B0B0B0}Down:${color #FFFFFF} ${downspeed} ${alignr}${color #B0B0B0}Up:${color #FFFFFF} ${upspeed}
${downspeedgraph 24,158 00D9FF 00D9FF} ${alignr}${upspeedgraph 24,158 FF6B9D FF6B9D}
${color #B0B0B0}Total Down:${color #FFFFFF} ${totaldown} ${alignr}${color #B0B0B0}Total Up:${color #FFFFFF} ${totalup}

${color #FFFFFF}${font Liberation Sans:bold:size=14}PROCESSES${font}${color}
${hr 2}
${color #B0B0B0}Total:${color #FFFFFF} $processes ${alignr}${color #B0B0B0}Running:${color #FFFFFF} $running_processes
${color #B0B0B0}${voffset 4}Name${alignr}CPU%${alignr}MEM%
${color #606060}${hr}
${color #E0E0E0}${top name 1}${alignr}${top cpu 1}%${alignr}${top mem 1}%
${color #C0C0C0}${top name 2}${alignr}${top cpu 2}%${alignr}${top mem 2}%
${color #A0A0A0}${top name 3}${alignr}${top cpu 3}%${alignr}${top mem 3}%
${color #808080}${top name 4}${alignr}${top cpu 4}%${alignr}${top mem 4}%
]]
