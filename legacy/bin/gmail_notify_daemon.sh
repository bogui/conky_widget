#!/bin/bash
# Gmail notification daemon
# Runs in background and checks for new emails periodically

# Source shell config to get environment variables
if [ -f ~/.zshrc ]; then
    source ~/.zshrc 2>/dev/null
elif [ -f ~/.bashrc ]; then
    source ~/.bashrc 2>/dev/null
fi

# Check interval in seconds (2 minutes)
CHECK_INTERVAL=120

# Run continuously
while true; do
    # Check for new emails (this will send notifications if new emails arrive)
    ~/.local/bin/gmail_unread.py count > /dev/null 2>&1
    
    # Wait before next check
    sleep $CHECK_INTERVAL
done
