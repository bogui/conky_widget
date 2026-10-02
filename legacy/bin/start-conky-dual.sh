#!/bin/bash
# Script to start Conky on both monitors

# Wait for display to be ready (important for autostart)
sleep 3

# Source shell config to get environment variables (like Gmail credentials)
if [ -f ~/.zshrc ]; then
    source ~/.zshrc 2>/dev/null
elif [ -f ~/.bashrc ]; then
    source ~/.bashrc 2>/dev/null
fi

# Kill any existing Conky instances
killall conky 2>/dev/null

# Wait a moment for processes to terminate
sleep 1

# Export environment variables for Conky processes
export GMAIL_USER GMAIL_PASSWORD OPENWEATHER_API_KEY

# Start Conky on Monitor 1 (system info)
nohup conky -c ~/.config/conky/conky-monitor1.conf -d > /dev/null 2>&1 &
sleep 0.5

# Start Conky on Monitor 2 (system info)
nohup conky -c ~/.config/conky/conky-monitor2.conf -d > /dev/null 2>&1 &
sleep 0.5

# Start Weather widgets (second row)
nohup conky -c ~/.config/conky/conky-weather.conf -d > /dev/null 2>&1 &
sleep 0.5
nohup conky -c ~/.config/conky/conky-weather-monitor2.conf -d > /dev/null 2>&1 &

echo "Conky started on both monitors with weather widgets"
