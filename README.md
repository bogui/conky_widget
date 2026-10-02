# conky_widget

Desktop widgets for GNOME on Wayland (conky runs through Xwayland): a system monitor and a
Bulgarian calendar + weather panel for Ruse, one pair per connected monitor, with Gmail unread
mail and desktop notifications.

```
conky/      system.lua, weather.lua (one config each; monitor from CONKY_HEAD), theme.lua
bin/        scripts, symlinked into ~/.local/bin by install.sh
systemd/    gmail-fetch.timer + .service (systemd user units)
autostart/  conky-widget.desktop.in (template; install.sh fills in $HOME)
legacy/     the setup this replaced (October 2026), kept for reference
REVIEW.md   the review of the old setup that led to this layout
```

## What you see

**System panel** (left): hostname, kernel, uptime, load; Gmail unread count and the newest
unread messages; CPU usage, frequency and temperature; GPU model, temperature, fan and power
state; RAM and swap; root filesystem; public IP, network speed graphs and totals; top processes.

**Calendar + weather panel** (right): date and ISO week in Bulgarian, a seconds clock, current
conditions with feels-like, humidity and wind, the next four 3-hour periods, and the next four
days with high/low and rain chance. Conditions are drawn as Nerd Font glyphs inline with the
text, so the layout never drifts.

## Requirements

- Fedora or any distro with **conky 1.20+** built with Lua and Xft (Fedora: `sudo dnf install conky`).
- **GNOME** (Mutter). Monitor detection and hot-plug use Mutter's D-Bus `DisplayConfig`
  interface. On another desktop set `CONKY_MONITORS=N` and skip the watcher.
- **python3** with **python3-gobject** (`gi`), both present on a stock GNOME install.
- **A Nerd Font**. The configs use `MesloLGS Nerd Font`; change `GLYPH_FONT` in
  `bin/weather_ruse.py` if you use another one. Fonts: <https://www.nerdfonts.com>.
- **Liberation Sans** for the text (any sans works; change `font` in the Lua configs).
- `notify-send` (libnotify), `curl`, `lspci` (pciutils).
- A **Gmail app password** (Google account → Security → 2-Step Verification → App passwords).
  The fetcher uses IMAP, so IMAP must be enabled in Gmail settings.
- An **OpenWeatherMap API key** (free tier is enough): <https://openweathermap.org/api>.
- The GPU section reads the **nouveau** driver's sysfs entries. With the proprietary NVIDIA
  driver or an AMD card, edit the GPU block in `conky/system.lua` (see "Adapting" below).

## Install

```
git clone https://github.com/bogui/conky_widget ~/dev/conky_widget
cd ~/dev/conky_widget
./install.sh
```

The installer symlinks scripts and configs into place, generates the autostart entry, creates
`~/.config/conky_widget/env` (mode 600) if missing, enables the Gmail timer and starts conky.
Fill in the credentials file, then run `~/.local/bin/gmail_fetch.py` once (or wait two minutes):

```
GMAIL_USER=you@gmail.com
GMAIL_PASSWORD=your-app-password
OPENWEATHER_API_KEY=your-key
```

Re-run `./install.sh` after editing anything in `systemd/` or `autostart/`. Config edits take
effect after `~/.local/bin/start-conky.sh`; script edits are picked up on their next run.

## How it fits together

- `conky-watch.sh` (autostart) runs `start-conky.sh`, then listens to Mutter's
  `MonitorsChanged` signal and restarts conky about three seconds after a monitor is plugged
  in or removed.
- `start-conky.sh` asks Mutter how many logical monitors there are and starts `system.lua`
  and `weather.lua` once per head (`CONKY_HEAD=0..N-1`). `CONKY_MONITORS=N` overrides it.
- `gmail_fetch.py` is the only process that talks to Gmail or sends notifications. The timer
  runs it every two minutes. It opens one read-only IMAP session, lists unread message UIDs,
  and announces each UID exactly once, however many times it runs and whatever else happens to
  the mailbox. State lives in `~/.cache/conky_widget/gmail_state.json`. The first run seeds the
  seen list silently.
- `gmail_render.py` turns that state file into conky markup. No network, no side effects,
  and it escapes `$` so a subject line can't be parsed as conky syntax.
- `weather_ruse.py` fetches OpenWeatherMap current + 5-day/3-hour forecast, caches for ten
  minutes, and emits the `current`, `details`, `today` and `week` blocks. Times use the city's
  own timezone offset from the API. The free forecast only covers four full future days.
- `gpu_info.sh` reads temperature, fan and power state from the nouveau hwmon/sysfs entries.
- `theme.lua` holds the colour helpers (`conky_bar_color`, `conky_temp_bar_color`,
  `conky_disk_bar_color`) used by the bars.

## Adapting

- **City**: `CITY` and `COUNTRY` at the top of `bin/weather_ruse.py`. Day names and labels are
  Bulgarian; `BG_DAYS` and the strings in `conky/weather.lua` are the places to translate.
- **Position**: `gap_x` / `gap_y` in each Lua config. `gap_y = 40` sits just under GNOME's
  32 px top bar. The weather panel's `gap_x = 400` places it right of the 330 px system panel.
- **CPU sensor**: `${hwmon coretemp temp 1}` (Intel). AMD is usually `k10temp`. Check
  `cat /sys/class/hwmon/hwmon*/name`.
- **GPU**: the block in `system.lua` uses `${hwmon nouveau temp 1}` and `gpu_info.sh`. For the
  NVIDIA proprietary driver use conky's `${nvidia ...}` variables; for AMD, `amdgpu` hwmon.
- **Check interval**: `OnUnitActiveSec` in `systemd/gmail-fetch.timer`. Keep the `execpi`
  intervals in `system.lua` at or below it.

## Useful commands

```
systemctl --user status gmail-fetch.timer     # is the timer running
journalctl --user -u gmail-fetch -n 20        # fetcher log
~/.local/bin/gmail_fetch.py                   # fetch now
~/.local/bin/gmail_render.py list             # markup conky will show
~/.local/bin/weather_ruse.py week             # same for the weather
~/.local/bin/start-conky.sh                   # restart the widgets
CONKY_MONITORS=2 ~/.local/bin/start-conky.sh  # force two heads
```

## Uninstall

```
systemctl --user disable --now gmail-fetch.timer
pkill -f conky-watch.sh; pkill -x conky
rm ~/.config/autostart/conky-widget.desktop ~/.config/conky/*.lua
rm ~/.config/systemd/user/gmail-fetch.* ~/.local/bin/{gmail_fetch.py,gmail_render.py,weather_ruse.py,gpu_info.sh,date_bg.py,get_public_ip.sh,start-conky.sh,conky-watch.sh}
rm -r ~/.cache/conky_widget           # and ~/.config/conky_widget/env if you want
```
