#!/bin/bash
# Install (symlink) the conky widget into the home directory and switch it on.
# Safe to re-run. Removes the pre-October-2026 files it replaces (backup in legacy/).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

link() { mkdir -p "$(dirname "$2")"; ln -sfn "$1" "$2"; echo "  $2 -> $1"; }

echo "== scripts"
for f in "$REPO"/bin/*; do
    chmod +x "$f"
    link "$f" "$HOME/.local/bin/$(basename "$f")"
done

echo "== conky configs"
for f in "$REPO"/conky/*.lua; do
    link "$f" "$HOME/.config/conky/$(basename "$f")"
done

echo "== systemd user units"
for f in "$REPO"/systemd/*; do
    link "$f" "$HOME/.config/systemd/user/$(basename "$f")"
done

echo "== autostart"
mkdir -p "$HOME/.config/autostart"
rm -f "$HOME/.config/autostart/conky-widget.desktop"
sed "s#@HOME@#$HOME#g" "$REPO/autostart/conky-widget.desktop.in" > "$HOME/.config/autostart/conky-widget.desktop"
echo "  $HOME/.config/autostart/conky-widget.desktop (generated)"

echo "== credentials"
ENV_FILE="$HOME/.config/conky_widget/env"
if [ ! -f "$ENV_FILE" ]; then
    mkdir -p "$(dirname "$ENV_FILE")"
    ( umask 077; printf 'GMAIL_USER=\nGMAIL_PASSWORD=\nOPENWEATHER_API_KEY=\n' > "$ENV_FILE" )
    echo "  created empty $ENV_FILE -- fill it in (mode 600)"
else
    chmod 600 "$ENV_FILE"; echo "  $ENV_FILE present"
fi

echo "== removing replaced legacy files"
for f in "$HOME"/.config/conky/conky-monitor1.conf "$HOME"/.config/conky/conky-monitor2.conf \
         "$HOME"/.config/conky/conky-weather.conf "$HOME"/.config/conky/conky-weather-monitor2.conf \
         "$HOME"/.config/conky/scripts/debug.lua \
         "$HOME"/.local/bin/gmail_unread.py "$HOME"/.local/bin/gmail_format_emails.sh \
         "$HOME"/.local/bin/gmail_notify_daemon.sh "$HOME"/.local/bin/start-conky-dual.sh \
         "$HOME"/.config/autostart/conky-dual.desktop "$HOME"/.config/autostart/gmail-notify.desktop \
         "$HOME"/.cache/gmail_unread_cache.json "$HOME"/.cache/gmail_previous_count.txt \
         "$HOME"/.cache/gmail_unread.lock "$HOME"/.cache/weather_ruse_cache.json; do
    [ -e "$f" ] && rm -f "$f" && echo "  removed $f"
done
rmdir "$HOME/.config/conky/scripts" 2>/dev/null || true
rm -rf "$HOME/.cache/weather_icons"

echo "== stopping old processes"
pkill -f gmail_notify_daemon.sh 2>/dev/null || true
pkill -x conky 2>/dev/null || true

echo "== enabling gmail timer"
systemctl --user daemon-reload
systemctl --user enable --now gmail-fetch.timer
systemctl --user start gmail-fetch.service || echo "  first fetch failed; see: journalctl --user -u gmail-fetch"

echo "== starting conky"
"$HOME/.local/bin/start-conky.sh"
echo "done"
