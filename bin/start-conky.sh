#!/bin/bash
# Start one system widget and one weather widget per connected monitor.
# Monitor count comes from GNOME Mutter over D-Bus (no xrandr needed under Wayland).
# Override with CONKY_MONITORS=N.

CONF_DIR="$HOME/.config/conky"

detect_monitors() {
    python3 - <<'EOF' 2>/dev/null
import gi
gi.require_version("Gio", "2.0")
from gi.repository import Gio
bus = Gio.bus_get_sync(Gio.BusType.SESSION)
r = bus.call_sync("org.gnome.Mutter.DisplayConfig", "/org/gnome/Mutter/DisplayConfig",
                  "org.gnome.Mutter.DisplayConfig", "GetCurrentState", None, None, 0, -1, None)
print(len(r.unpack()[2]))   # logical monitors
EOF
}

n="${CONKY_MONITORS:-$(detect_monitors)}"
[[ "$n" =~ ^[0-9]+$ ]] && [ "$n" -ge 1 ] || n=1

# Replace whatever is running
pkill -x conky 2>/dev/null
sleep 0.5

for ((head = 0; head < n; head++)); do
    CONKY_HEAD=$head nohup conky -c "$CONF_DIR/system.lua"  -d >/dev/null 2>&1 &
    CONKY_HEAD=$head nohup conky -c "$CONF_DIR/weather.lua" -d >/dev/null 2>&1 &
done

echo "conky started on $n monitor(s)"
