#!/bin/bash
# Get public IP address with caching
# Uses multiple services for reliability

CACHE_FILE="$HOME/.cache/public_ip_cache.txt"
CACHE_DURATION=600  # Cache for 10 minutes

# Check cache first
if [ -f "$CACHE_FILE" ]; then
    cache_time=$(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null)
    current_time=$(date +%s)
    age=$((current_time - cache_time))
    
    if [ $age -lt $CACHE_DURATION ]; then
        cat "$CACHE_FILE"
        exit 0
    fi
fi

# Try multiple services for reliability
get_ip() {
    # Try ipify.org first (fast and reliable)
    ip=$(curl -s --max-time 3 https://api.ipify.org 2>/dev/null)
    if [ -n "$ip" ] && [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo "$ip" > "$CACHE_FILE"
        echo "$ip"
        exit 0
    fi
    
    # Fallback to ifconfig.me
    ip=$(curl -s --max-time 3 https://ifconfig.me 2>/dev/null)
    if [ -n "$ip" ] && [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo "$ip" > "$CACHE_FILE"
        echo "$ip"
        exit 0
    fi
    
    # Last fallback to icanhazip.com
    ip=$(curl -s --max-time 3 https://icanhazip.com 2>/dev/null)
    if [ -n "$ip" ] && [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo "$ip" > "$CACHE_FILE"
        echo "$ip"
        exit 0
    fi
    
    # If all fail, return cached value or "N/A"
    if [ -f "$CACHE_FILE" ]; then
        cat "$CACHE_FILE"
    else
        echo "N/A"
    fi
}

get_ip
