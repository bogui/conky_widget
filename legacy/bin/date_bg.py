#!/usr/bin/env python3
"""
Bulgarian date and time formatter for Conky
"""

import sys
from datetime import datetime
import locale

# Bulgarian month and day names
BG_MONTHS = [
    'януари', 'февруари', 'март', 'април', 'май', 'юни',
    'юли', 'август', 'септември', 'октомври', 'ноември', 'декември'
]

BG_DAYS = [
    'Понеделник', 'Вторник', 'Сряда', 'Четвъртък',
    'Петък', 'Събота', 'Неделя'
]

BG_DAYS_SHORT = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']

def get_calendar_week(date):
    """Calculate ISO calendar week number"""
    return date.isocalendar()[1]

def format_date_bg(date=None):
    """Format date in Bulgarian format"""
    if date is None:
        date = datetime.now()
    
    day = date.day
    month = BG_MONTHS[date.month - 1]
    year = date.year
    day_name = BG_DAYS[date.weekday()]
    
    return f"{day_name}, {day} {month} {year}"

def format_time_bg(date=None):
    """Format time in Bulgarian format"""
    if date is None:
        date = datetime.now()
    
    return date.strftime('%H:%M:%S')

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'date'
    now = datetime.now()
    
    if mode == 'date':
        print(format_date_bg(now))
    elif mode == 'time':
        print(format_time_bg(now))
    elif mode == 'week':
        print(f"Седмица {get_calendar_week(now)}")
    elif mode == 'all':
        print(format_date_bg(now))
        print(format_time_bg(now))
        print(f"Седмица {get_calendar_week(now)}")
