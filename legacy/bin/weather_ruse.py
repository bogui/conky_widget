#!/usr/bin/env python3
"""
Weather script for Ruse, Bulgaria
Fetches weather data and formats it for Conky display
"""

import json
import sys
import os
import time
from pathlib import Path
from datetime import datetime
import urllib.request
import urllib.error

# Configuration
CITY = "Ruse"
COUNTRY_CODE = "BG"
CACHE_FILE = Path.home() / '.cache' / 'weather_ruse_cache.json'
CACHE_DURATION = 600  # Cache for 10 minutes

# Weather API - using OpenWeatherMap (free tier)
# Using 3-hour forecast endpoint (5 days available on free plan)
# You'll need to get an API key from https://openweathermap.org/api

def get_api_key():
    """Get API key from environment"""
    return os.environ.get('OPENWEATHER_API_KEY', '')

def get_current_url():
    """Get current weather URL with API key"""
    api_key = get_api_key()
    return f"https://api.openweathermap.org/data/2.5/weather?q={CITY},{COUNTRY_CODE}&appid={api_key}&units=metric&lang=bg"

def get_forecast_url():
    """Get forecast URL with API key"""
    api_key = get_api_key()
    return f"https://api.openweathermap.org/data/2.5/forecast?q={CITY},{COUNTRY_CODE}&appid={api_key}&units=metric&lang=bg"

# Icon cache directory
ICON_CACHE_DIR = Path.home() / '.cache' / 'weather_icons'

# Conky formatting constants
CONKY_COLOR_E0E0E0 = "${color #E0E0E0}"
CONKY_COLOR_RESET = "${color}"
CONKY_COLOR_WHITE = "${color #FFFFFF}"
CONKY_IMAGE_START = "${image "
# Image positioning: X position after text (60px), Y will be calculated per line
# Line height is approximately 20px, starting at ~200px (after headers)
CONKY_IMAGE_X_POS = 40  # Horizontal position after time/day text
CONKY_IMAGE_Y_START = 210  # Starting Y position for first forecast item
CONKY_LINE_HEIGHT = 15  # Approximate line height
CONKY_IMAGE_TAG_SMALL = " -s 24x24}"
CONKY_IMAGE_TAG_LARGE = " -s 48x48}"
CONKY_DEGREE_SUFFIX = "°${color}"

def get_icon_url(icon_code):
    """
    Get OpenWeatherMap icon URL
    Note: OpenWeatherMap only supports @2x resolution now
    """
    return f"http://openweathermap.org/img/wn/{icon_code}@2x.png"

def get_icon_path(icon_code):
    """
    Get local cached icon path, download if not exists
    Returns path suitable for Conky ${image} tag
    """
    ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    icon_filename = f"{icon_code}@2x.png"
    icon_path = ICON_CACHE_DIR / icon_filename

    # Download icon if not cached
    if not icon_path.exists():
        try:
            icon_url = get_icon_url(icon_code)
            urllib.request.urlretrieve(icon_url, icon_path)
        except Exception as e:
            print(f"Warning: Could not download icon {icon_code}: {e}", file=sys.stderr)
            # Return URL as fallback
            return get_icon_url(icon_code)

    return str(icon_path)

def get_icon_for_conky(icon_code, use_local_cache=True):
    """
    Get icon path/URL formatted for Conky ${image} tag
    If use_local_cache is True, returns local path, otherwise returns URL
    """
    if use_local_cache:
        return get_icon_path(icon_code)
    else:
        return get_icon_url(icon_code)

def get_cached_weather():
    """Get cached weather data if still valid"""
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
            cache_time = cache_data.get('timestamp', 0)
            current_time = time.time()

            if current_time - cache_time < CACHE_DURATION:
                return cache_data.get('data')
    except Exception:
        pass

    return None

def save_cache(weather_data):
    """Save weather data to cache"""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {
            'timestamp': time.time(),
            'data': weather_data
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception:
        pass

def fetch_current_weather():
    """Fetch current weather data"""
    api_key = get_api_key()
    if not api_key:
        return None

    try:
        url = get_current_url()
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"Weather API Error: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error fetching current weather: {e}", file=sys.stderr)
        return None

def fetch_forecast():
    """Fetch 3-hour forecast data (5 days)"""
    api_key = get_api_key()
    if not api_key:
        return None

    try:
        url = get_forecast_url()
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"Weather API Error: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error fetching forecast: {e}", file=sys.stderr)
        return None

def format_weather_for_conky():
    """Format weather data for Conky display"""
    # Check cache first
    cached_data = get_cached_weather()

    if not cached_data:
        # Fetch current weather and forecast
        current_data = fetch_current_weather()
        forecast_data = fetch_forecast()

        if current_data and forecast_data:
            combined_data = {
                'current': current_data,
                'forecast': forecast_data
            }
            save_cache(combined_data)
            cached_data = combined_data
        else:
            return None

    if not cached_data:
        return None

    try:
        current = cached_data.get('current', {})
        forecast_list = cached_data.get('forecast', {}).get('list', [])

        if not current or not forecast_list:
            return None

        # Current weather
        temp = int(current['main']['temp'])
        feels_like = int(current['main']['feels_like'])
        description = current['weather'][0]['description'].title()
        icon_code = current['weather'][0]['icon']
        icon_path = get_icon_for_conky(icon_code, use_local_cache=True)
        humidity = current['main']['humidity']

        # Today's forecast (next 3-hour periods)
        today_forecast = []
        current_date = datetime.now().date()
        current_hour = datetime.now().hour

        # Get next 4 periods (12 hours)
        line_index = 0
        for item in forecast_list[:8]:
            item_time = datetime.fromtimestamp(item['dt'])
            if item_time.date() == current_date and item_time.hour >= current_hour:
                temp_item = int(item['main']['temp'])
                icon_code = item['weather'][0]['icon']
                icon_path = get_icon_for_conky(icon_code, use_local_cache=True)
                time_str = item_time.strftime('%H:%M')
                # Calculate Y position based on line index
                y_pos = CONKY_IMAGE_Y_START + (line_index * CONKY_LINE_HEIGHT)
                # Format: time text, then image at fixed X with calculated Y, then temperature
                image_tag = CONKY_IMAGE_START + icon_path + f" -p {CONKY_IMAGE_X_POS},{y_pos}" + CONKY_IMAGE_TAG_SMALL
                today_forecast.append(CONKY_COLOR_E0E0E0 + time_str + CONKY_COLOR_RESET + " " + image_tag + " ${offset 30}" + CONKY_COLOR_WHITE + str(temp_item) + CONKY_DEGREE_SUFFIX)
                line_index += 1
                if len(today_forecast) >= 4:
                    break

        # Week forecast (one per day from 3-hour forecast)
        # Y position starts after today forecast (4 lines * 20px = 80px offset)
        week_y_start = CONKY_IMAGE_Y_START + (5.5 * CONKY_LINE_HEIGHT)
        week_forecast = []
        seen_dates = set()
        current_date_obj = datetime.now().date()
        week_line_index = 0

        for item in forecast_list:
            item_time = datetime.fromtimestamp(item['dt'])
            date_key = item_time.date()

            # Skip today, get one forecast per day (prefer afternoon times)
            if date_key > current_date_obj and date_key not in seen_dates:
                if 12 <= item_time.hour <= 15:  # Prefer afternoon
                    seen_dates.add(date_key)
                    temp_day = int(item['main']['temp'])
                    icon_code = item['weather'][0]['icon']
                    icon_path = get_icon_for_conky(icon_code, use_local_cache=True)
                    # Use Bulgarian day names
                    bg_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
                    day_name = bg_days[item_time.weekday()]
                    # Calculate Y position based on line index
                    y_pos = week_y_start + (week_line_index * CONKY_LINE_HEIGHT)
                    image_tag = CONKY_IMAGE_START + icon_path + f" -p {CONKY_IMAGE_X_POS - 15},{y_pos}" + CONKY_IMAGE_TAG_SMALL
                    week_forecast.append(CONKY_COLOR_E0E0E0 + day_name + CONKY_COLOR_RESET + " " + image_tag + " ${offset 30}" + CONKY_COLOR_WHITE + str(temp_day) + CONKY_DEGREE_SUFFIX)
                    week_line_index += 1
                    if len(week_forecast) >= 5:  # 5 days
                        break

        # If we don't have enough afternoon forecasts, get any one per day
        if len(week_forecast) < 5:
            seen_dates = {current_date_obj}
            for item in forecast_list:
                item_time = datetime.fromtimestamp(item['dt'])
                date_key = item_time.date()
                if date_key > current_date_obj and date_key not in seen_dates:
                    seen_dates.add(date_key)
                    temp_day = int(item['main']['temp'])
                    icon_code = item['weather'][0]['icon']
                    icon_path = get_icon_for_conky(icon_code, use_local_cache=True)
                    bg_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
                    day_name = bg_days[item_time.weekday()]
                    # Calculate Y position based on line index
                    y_pos = week_y_start + (week_line_index * CONKY_LINE_HEIGHT)
                    image_tag = CONKY_IMAGE_START + icon_path + f" -p {CONKY_IMAGE_X_POS - 15},{y_pos}" + CONKY_IMAGE_TAG_SMALL
                    week_forecast.append(CONKY_COLOR_E0E0E0 + day_name + CONKY_COLOR_RESET + " " + image_tag + " ${offset 27}" + CONKY_COLOR_WHITE + str(temp_day) + CONKY_DEGREE_SUFFIX)
                    week_line_index += 1
                    if len(week_forecast) >= 5:
                        break

        return {
            'current': {
                'temp': temp,
                'feels_like': feels_like,
                'description': description,
                'icon': icon_path,
                'icon_code': icon_code,
                'humidity': humidity
            },
            'today_forecast': today_forecast[:4],  # Next 4 periods
            'week_forecast': week_forecast
        }
    except Exception as e:
        print(f"Error parsing weather: {e}", file=sys.stderr)
        return None

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'current'

    weather = format_weather_for_conky()
    if not weather:
        if mode == 'current':
            print("N/A")
        sys.exit(1)

    if mode == 'current':
        curr = weather['current']
        # Use ${image} tag for weather icon (2x size for current weather)
        print(CONKY_IMAGE_START + curr['icon'] + " -p 180,135" + CONKY_IMAGE_TAG_LARGE + " " + CONKY_COLOR_WHITE + str(curr['temp']) + "°C${color} ${color #B0B0B0}(" + str(curr['feels_like']) + "°C)${color} " + CONKY_COLOR_E0E0E0 + curr['description'] + CONKY_COLOR_RESET)
    elif mode == 'today':
        for item in weather['today_forecast']:
            print(item)
    elif mode == 'week':
        for item in weather['week_forecast']:
            print(item)
    elif mode == 'json':
        print(json.dumps(weather))
