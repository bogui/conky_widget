#!/bin/bash
# Format Gmail emails for Conky display
# Outputs sender and subject with Conky color codes

~/.local/bin/gmail_unread.py emails 2>/dev/null | head -5 | while IFS='|' read -r sender subject; do
    if [ -n "$sender" ] && [ -n "$subject" ]; then
        # Output with Conky color variables (they will be processed by Conky)
        printf '${color #E0E0E0}%s${color}\n' "${sender}"
        printf '${color #B0B0B0}  %s${color}\n' "${subject}"
    fi
done
