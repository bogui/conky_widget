# conky_widget

Desktop widgets for GNOME (Wayland, via Xwayland): system monitor + Bulgarian calendar and
weather for Ruse, one pair per connected monitor.

```
conky/      system.lua, weather.lua (one config each; monitor from CONKY_HEAD), theme.lua
bin/        scripts symlinked into ~/.local/bin
systemd/    gmail-fetch.timer + .service (user units)
autostart/  conky-widget.desktop.in (template; install.sh fills in $HOME)
legacy/     the setup this replaced (October 2026), kept for reference
REVIEW.md   the review that led to this layout
```

## Install

```
./install.sh
```

Symlinks everything into place, enables the Gmail timer, and starts conky. Re-run after
editing anything in `systemd/` or `autostart/`; config and script edits are picked up by
`start-conky.sh` (configs) or immediately (scripts).

Credentials live in `~/.config/conky_widget/env` (mode 600):

```
GMAIL_USER=you@gmail.com
GMAIL_PASSWORD=app-password
OPENWEATHER_API_KEY=...
```

## How it fits together

- `conky-watch.sh` runs `start-conky.sh`, then listens to Mutter's `MonitorsChanged` D-Bus
  signal and restarts conky when a monitor is plugged or unplugged.
- `start-conky.sh` asks Mutter how many logical monitors exist and starts `system.lua` and
  `weather.lua` once per head (`CONKY_HEAD=0..N-1`). `CONKY_MONITORS=N` overrides detection.
- `gmail_fetch.py` is the only thing that talks to Gmail or sends notifications. The timer runs
  it every 2 minutes. It tracks unread message UIDs in `~/.cache/conky_widget/gmail_state.json`
  and announces each UID once. `gmail_render.py` turns that file into conky markup.
- `weather_ruse.py` caches OpenWeatherMap for 10 minutes and draws conditions as Nerd Font
  glyphs inline with the text, so nothing is positioned by pixel.
- `gpu_info.sh` reads the nouveau hwmon/sysfs entries (temperature, fan, power state).

## Useful commands

```
systemctl --user status gmail-fetch.timer
journalctl --user -u gmail-fetch -n 20
~/.local/bin/gmail_fetch.py            # fetch now
~/.local/bin/weather_ruse.py week      # inspect markup
~/.local/bin/start-conky.sh            # restart widgets
```
