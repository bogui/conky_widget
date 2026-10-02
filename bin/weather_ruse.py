#!/usr/bin/env python3
"""
Weather for Ruse, Bulgaria, rendered for conky with inline Nerd Font glyphs.

Icons are glyphs in the text flow (no ${image} with pixel coordinates), so the
layout can never drift when the number of forecast lines changes.

  weather_ruse.py current   -> one line: glyph, temp, feels-like, description
  weather_ruse.py details   -> one line: humidity, wind
  weather_ruse.py today     -> next 4 three-hour periods
  weather_ruse.py week      -> next full days (max 4 with the free 5-day API)

API key: OPENWEATHER_API_KEY in ~/.config/conky_widget/env (or the environment).
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CITY, COUNTRY = "Ruse", "BG"
ENV_FILE = Path.home() / ".config" / "conky_widget" / "env"
CACHE_FILE = Path.home() / ".cache" / "conky_widget" / "weather_ruse.json"
CACHE_SECONDS = 600
TODAY_PERIODS = 4
WEEK_DAYS = 4
MIN_PERIODS_FOR_DAY = 6     # a "full" day has 8 three-hour periods; tolerate a missing couple

GLYPH_FONT = "MesloLGS Nerd Font"
GLYPH_SIZE = 11
GLYPH_SIZE_BIG = 16

# OpenWeatherMap icon code -> Nerd Font weather glyph (verified against glyphnames.json)
GLYPHS = {
    "01d": 0xE30D, "01n": 0xE32B,   # clear
    "02d": 0xE302, "02n": 0xE37E,   # few clouds
    "03d": 0xE33D, "03n": 0xE33D,   # scattered clouds
    "04d": 0xE312, "04n": 0xE312,   # broken / overcast
    "09d": 0xE309, "09n": 0xE326,   # showers
    "10d": 0xE308, "10n": 0xE325,   # rain
    "11d": 0xE30F, "11n": 0xE32A,   # thunderstorm
    "13d": 0xE30A, "13n": 0xE327,   # snow
    "50d": 0xE303, "50n": 0xE346,   # mist / fog
}
GLYPH_UNKNOWN = 0xE33D
GLYPH_RAIN_CHANCE = 0xE34A         # raindrops

BG_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]

C_LABEL = "${color #E0E0E0}"
C_VALUE = "${color #FFFFFF}"
C_DIM = "${color #B0B0B0}"
C_WARN = "${color #FB9905}"
C_END = "${color}"

# Columns (pixels from the window's left edge) for the forecast rows
COL_LABEL, COL_GLYPH, COL_TEMP, COL_EXTRA = 0, 52, 80, 150


def load_env():
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                values[k.strip()] = v.strip().strip("'\"")
    if os.environ.get("OPENWEATHER_API_KEY"):
        values["OPENWEATHER_API_KEY"] = os.environ["OPENWEATHER_API_KEY"]
    return values


def glyph(icon_code, size=GLYPH_SIZE):
    cp = GLYPHS.get(icon_code, GLYPH_UNKNOWN)
    return f"${{font {GLYPH_FONT}:size={size}}}{chr(cp)}${{font}}"


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode())


def get_data():
    """Return {'current':..., 'forecast':...} from cache or the API (cached on success)."""
    cached = None
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            cached = json.load(f)
        if time.time() - cached.get("timestamp", 0) < CACHE_SECONDS:
            return cached["data"], False
    except Exception:
        cached = None

    key = load_env().get("OPENWEATHER_API_KEY", "")
    if not key:
        print("OPENWEATHER_API_KEY missing", file=sys.stderr)
        return (cached["data"] if cached else None), True

    base = "https://api.openweathermap.org/data/2.5/"
    q = f"?q={CITY},{COUNTRY}&appid={key}&units=metric&lang=bg"
    try:
        data = {"current": fetch_json(base + "weather" + q),
                "forecast": fetch_json(base + "forecast" + q)}
    except Exception as e:
        print(f"Weather API error: {e}", file=sys.stderr)
        return (cached["data"] if cached else None), True   # stale data beats nothing

    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"timestamp": time.time(), "data": data}, f)
        os.replace(tmp, CACHE_FILE)
    except Exception:
        pass
    return data, False


def local_tz(data):
    offset = data.get("forecast", {}).get("city", {}).get("timezone")
    if offset is None:
        offset = data.get("current", {}).get("timezone", 0)
    return timezone(timedelta(seconds=offset))


def fmt_current(data):
    cur = data["current"]
    w = cur["weather"][0]
    temp = round(cur["main"]["temp"])
    feels = round(cur["main"]["feels_like"])
    desc = w["description"].capitalize()
    return (f"{glyph(w['icon'], GLYPH_SIZE_BIG)} {C_VALUE}{temp}°C{C_END} "
            f"{C_DIM}({feels}°C){C_END} {C_LABEL}{desc}{C_END}")


def fmt_details(data):
    cur = data["current"]
    hum = cur["main"].get("humidity")
    wind = cur.get("wind", {}).get("speed", 0)
    parts = []
    if hum is not None:
        parts.append(f"{C_DIM}Влажност:{C_END} {C_VALUE}{hum}%{C_END}")
    parts.append(f"{C_DIM}Вятър:{C_END} {C_VALUE}{round(wind * 3.6)} km/h{C_END}")
    return "   ".join(parts)


def fmt_period(item, tz):
    t = datetime.fromtimestamp(item["dt"], tz)
    pop = round(item.get("pop", 0) * 100)
    extra = f"${{goto {COL_EXTRA}}}{C_DIM}{pop}%{C_END}" if pop >= 10 else ""
    return (f"${{goto {COL_LABEL}}}{C_LABEL}{t.strftime('%H:%M')}{C_END}"
            f"${{goto {COL_GLYPH}}}{glyph(item['weather'][0]['icon'])}"
            f"${{goto {COL_TEMP}}}{C_VALUE}{round(item['main']['temp'])}°{C_END}{extra}")


def fmt_today(data):
    tz = local_tz(data)
    now = datetime.now(tz)
    upcoming = [i for i in data["forecast"]["list"]
                if datetime.fromtimestamp(i["dt"], tz) > now - timedelta(hours=1)]
    return [fmt_period(i, tz) for i in upcoming[:TODAY_PERIODS]]


def fmt_week(data):
    tz = local_tz(data)
    today = datetime.now(tz).date()
    by_day = {}
    for item in data["forecast"]["list"]:
        t = datetime.fromtimestamp(item["dt"], tz)
        if t.date() > today:
            by_day.setdefault(t.date(), []).append((t, item))

    lines = []
    for day in sorted(by_day):
        periods = by_day[day]
        if len(periods) < MIN_PERIODS_FOR_DAY:
            continue
        # icon from the period closest to 13:00, temps across the whole day
        t_icon, icon_item = min(periods, key=lambda p: abs(p[0].hour - 13))
        hi = round(max(p[1]["main"]["temp_max"] for p in periods))
        lo = round(min(p[1]["main"]["temp_min"] for p in periods))
        pop = round(max(p[1].get("pop", 0) for p in periods) * 100)
        extra = f"${{goto {COL_EXTRA}}}{C_DIM}{pop}%{C_END}" if pop >= 10 else ""
        lines.append(
            f"${{goto {COL_LABEL}}}{C_LABEL}{BG_DAYS[day.weekday()]}{C_END}"
            f"${{goto {COL_GLYPH}}}{glyph(icon_item['weather'][0]['icon'])}"
            f"${{goto {COL_TEMP}}}{C_VALUE}{hi}°{C_END}{C_DIM}/{lo}°{C_END}{extra}"
        )
        if len(lines) >= WEEK_DAYS:
            break
    return lines


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "current"
    data, stale = get_data()
    if not data:
        if mode == "current":
            print(f"{C_WARN}няма данни{C_END}")
        return 1
    try:
        if mode == "current":
            print(fmt_current(data) + (f" {C_WARN}(стари данни){C_END}" if stale else ""))
        elif mode == "details":
            print(fmt_details(data))
        elif mode == "today":
            print("\n".join(fmt_today(data)))
        elif mode == "week":
            print("\n".join(fmt_week(data)))
        elif mode == "json":
            print(json.dumps(data, ensure_ascii=False))
        else:
            print(f"unknown mode {mode}", file=sys.stderr)
            return 2
    except Exception as e:
        print(f"Error formatting weather: {e}", file=sys.stderr)
        if mode == "current":
            print(f"{C_WARN}грешка{C_END}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
