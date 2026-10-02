#!/bin/bash
# Session entry point (autostart): start conky, then restart it whenever
# monitors are plugged or unplugged (Mutter emits MonitorsChanged).

sleep 3                       # let the desktop settle after login
"$HOME/.local/bin/start-conky.sh"

pending=""
gdbus monitor --session --dest org.gnome.Mutter.DisplayConfig \
      --object-path /org/gnome/Mutter/DisplayConfig 2>/dev/null |
while read -r line; do
    case "$line" in
        *MonitorsChanged*)
            # debounce: several signals arrive in a burst while GNOME reconfigures
            [ -n "$pending" ] && kill "$pending" 2>/dev/null
            ( sleep 3; "$HOME/.local/bin/start-conky.sh" ) &
            pending=$!
            ;;
    esac
done
