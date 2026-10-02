# Conky widget review (2026-10-02)

**Status (2026-10-02):** implemented. The layout below is live; see README.md. The old files are in `legacy/`.

Live files reviewed:

- `~/.config/conky/conky-monitor1.conf`, `conky-monitor2.conf`, `conky-weather.conf`, `conky-weather-monitor2.conf`, `scripts/debug.lua`
- `~/.local/bin/gmail_unread.py`, `gmail_format_emails.sh`, `gmail_notify_daemon.sh`, `get_public_ip.sh`, `date_bg.py`, `weather_ruse.py`, `start-conky-dual.sh`
- `~/.config/autostart/conky-dual.desktop`, `gmail-notify.desktop`
- Runtime: conky 1.22.2, GNOME 50.5 on Wayland (conky runs through Xwayland), Python 3.14, Nerd Fonts (Meslo) installed.

## Bug 1: repeated Gmail notifications

Root cause: five independent processes all run the same script, and each one is allowed to notify.

| Caller | Mode | Interval |
|---|---|---|
| conky-monitor1 `execpi` | count | 120 s |
| conky-monitor1 `execpi` (via gmail_format_emails.sh) | emails | 120 s |
| conky-monitor2 `execpi` | count | 120 s |
| conky-monitor2 `execpi` (via gmail_format_emails.sh) | emails | 120 s |
| gmail_notify_daemon.sh | count | 120 s |

The cache lasts 60 s, the two conky instances start 0.5 s apart, and an IMAP session takes several seconds. So on every cycle both conky instances miss the cache, both read the same "previous count", both fetch, and both notify for the same email. The daemon runs on its own phase and adds a third. A slower process that finishes after a faster one can write a stale, lower previous count, so the next cycle notifies again. GNOME ignores the `-t 10000` timeout, so the duplicates stack up in the notification tray.

Other defects in the same script:

- The lock file is only checked after a cache miss and then falls through, so it never serializes anything. Each process also deletes the other's lock in `finally`.
- Detection is count-based. Reading one email while another arrives hides the new one. Deleting or archiving then receiving re-notifies.
- "Recent Emails" and the notification text come from the last 5 messages overall (`search ALL`), not from the unread ones, so a notification can name the wrong mail.
- `emails` mode crashes with `NameError` on `emails` when the count fetch returns -1 (network blip, Gmail "too many simultaneous connections").
- Sender and subject are injected into conky markup unescaped. A subject containing `$` or `${...}` is parsed by conky. `$` must be doubled.
- Two IMAP logins per run, times five callers. Gmail allows 15 concurrent IMAP connections per account.

### Proposed fix

Split fetching from displaying.

1. One fetcher only: `gmail_fetch.py`, run by a systemd user timer every 2 minutes (replaces the daemon loop and the autostart entry). One IMAP session, read-only select, `UID SEARCH UNSEEN`, fetch headers of the unread UIDs only.
2. State file `~/.cache/gmail_state.json`: `{count, unread: [{uid, sender, subject}], seen_uids: [...]}`. Notify only for UIDs that are not in `seen_uids`. Re-notification becomes impossible, and reading, archiving or deleting mail cannot confuse it.
3. Conky reads the state file with a tiny side-effect-free renderer (`gmail_render.py count|list`). Delete `gmail_unread.py`, `gmail_format_emails.sh`, `gmail_notify_daemon.sh`, the lock file and the previous-count file.
4. Escape `$` as `$$` in the renderer. Use `-h string:desktop-entry` and a stable `--app-name` with notify-send so GNOME groups them.
5. Credentials: move them out of `.zshrc` into `~/.config/gmail_credentials` (mode 600, the script already supports it), or `secret-tool`. Then nothing needs to source `.zshrc` from bash.

## Bug 2: weather icons drift in the afternoon

Root cause: the icons are placed with absolute pixel coordinates (`${image ... -p X,Y}`) while the text flows. The "Днес" block has a variable number of lines (4 in the morning, 2 at 18:00, 0 after 21:00), but the week block's start Y is hard-coded as `210 + 5.5 * 15`. Fewer "today" lines move the text up while the icons stay put, so they land one or two rows low.

Secondary causes that cause drift even in the morning:

- The script assumes a 15 px line height. The real line height is 16 px (screenshot: 09:00 at y=192, 12:00 at y=208). Icons drift one pixel per line.
- The week Y comes out as a float (292.5).
- A long "Сега" description that wraps shifts everything by a row at any time of day.
- The duplicate "Сб 12°" at the bottom of the week list is a separate bug: the fallback loop resets `seen_dates` but not `week_forecast`, so it appends the first future day again. The 5-day forecast only has 4 full future days, so the fifth day never has an afternoon period and the fallback runs every time.
- After 21:00 "Днес" is empty.

### Proposed fix

Minimal (one line): compute `week_y_start = Y_START + (len(today_forecast) + 1) * LINE_HEIGHT` and set `LINE_HEIGHT = 16`. That fixes the afternoon shift but keeps the pixel coupling.

Recommended: drop the PNG images and render the condition as an inline glyph from the installed Nerd Font, so icons flow with the text and nothing is positioned by pixel. Verified codepoints from the Nerd Fonts glyph list:

| OWM icon | Glyph | Codepoint |
|---|---|---|
| 01d / 01n | day_sunny / night_clear | U+E30D / U+E32B |
| 02d / 02n | day_cloudy / night_alt_cloudy | U+E302 / U+E37E |
| 03d, 03n | cloud | U+E33D |
| 04d, 04n | cloudy | U+E312 |
| 09d / 09n | day_showers / night_alt_showers | U+E309 / U+E326 |
| 10d / 10n | day_rain / night_alt_rain | U+E308 / U+E325 |
| 11d / 11n | day_thunderstorm / night_alt_thunderstorm | U+E30F / U+E32A |
| 13d / 13n | day_snow / night_alt_snow | U+E30A / U+E327 |
| 50d / 50n | day_fog / night_fog | U+E303 / U+E346 |

Each line becomes: `${goto 0}09:00 ${font MesloLGS Nerd Font:size=12}<glyph>${font} ${goto 90}13°`.

Also in the weather script:

- Group forecast periods by local date, pick the period nearest 13:00 for the icon, and show daily min/max (e.g. `Сб  18°/9°`). Show the 4 full days honestly instead of a partial fifth.
- "Днес": show the next 4 periods regardless of date, labelled by hour; after 21:00 this naturally shows tomorrow morning.
- Add rain probability (`pop`) and wind, both already in the response.
- Use `datetime.fromtimestamp(dt, tz=...)` with the `city.timezone` offset so the output does not depend on the machine's zone.
- Use `https://` for the icon URL (still used by the minimal fix).

## Other findings

- **CPU temperature shows the GPU.** `hwmon 0` is `nouveau` (47 °C in the screenshot). The CPU is `hwmon2 coretemp` (31 °C). Use `${hwmon coretemp temp 1}`; numeric indices reorder across boots.
- **Two near-identical monitor configs** (and two weather configs) differ only in `xinerama_head` and one network graph. Make one Lua config that reads the head from an env var (`CONKY_HEAD`), and start it twice.
- **`~/.conkyrc`** is the stock default and is never used by the start script. Delete or ignore.
- **`update_interval = 2.0`** makes the seconds clock skip every other second. Use 1.0 on the weather config, or drop seconds.
- **Credentials in `.zshrc`** are exported into every shell and child process, and `GMAIL_USER` is defined twice (lines 235-236). Move to a 600 file or the keyring.
- **`start-conky-dual.sh` sources `.zshrc` from bash.** It works today by luck. It is unnecessary once credentials come from a file.
- **`debug.lua`** has leftover debug helpers and a dead return after the if-chain. The bar colour function uses dark shades (e.g. `#223374` at 16-25 %) that are nearly invisible on the blue wallpaper. A smooth gradient or three fixed colours would read better.
- **`get_public_ip.sh`** is fine. Consider 10 minutes instead of 5 and `curl --max-time 3`.
- **`date_bg.py`** is fine. `time_bg` and `all` modes are unused.
- **Native Wayland**: conky 1.22 can do `out_to_wayland = true`, which avoids Xwayland and the desktop-window hints that GNOME only half honours. Worth a try later, not a fix for either bug.

## Proposed layout for this repository

```
conky_widget/
  conky/
    system.lua        # one config, head from CONKY_HEAD
    weather.lua
    theme.lua         # colours, fonts, bar helpers (replaces debug.lua)
  bin/
    gmail_fetch.py    # timer-driven fetcher + notifier (UID based)
    gmail_render.py   # side-effect-free renderer for conky
    weather_ruse.py   # glyph version
    date_bg.py
    get_public_ip.sh
    start-conky.sh
  systemd/
    gmail-fetch.service
    gmail-fetch.timer
    conky.service     # replaces the autostart .desktop
  install.sh          # symlinks into ~/.config/conky, ~/.local/bin, ~/.config/systemd/user
  README.md
```
