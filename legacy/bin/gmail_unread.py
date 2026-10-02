#!/usr/bin/env python3
"""
Gmail Unread Email Counter for Conky
Uses IMAP to fetch unread email count from Gmail
Includes file-based caching to prevent multiple API calls
"""

import imaplib
import sys
import os
import time
import json
import email
import subprocess
from pathlib import Path
from email.header import decode_header

# Try to load credentials from multiple sources
GMAIL_USER = ''
GMAIL_PASSWORD = ''

# 1. Try environment variables first
GMAIL_USER = os.environ.get('GMAIL_USER', '')
GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD', '')

# 2. If not set, try credentials file
if not GMAIL_USER or not GMAIL_PASSWORD:
    creds_file = Path.home() / '.config' / 'gmail_credentials'
    if creds_file.exists():
        try:
            with open(creds_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GMAIL_USER='):
                        GMAIL_USER = line.split('=', 1)[1].strip("'\"")
                    elif line.startswith('GMAIL_PASSWORD='):
                        GMAIL_PASSWORD = line.split('=', 1)[1].strip("'\"")
        except Exception as e:
            pass

# Cache settings
CACHE_FILE = Path.home() / '.cache' / 'gmail_unread_cache.json'
CACHE_DURATION = 60  # Cache for 1 minute (60 seconds) - faster updates
LOCK_FILE = Path.home() / '.cache' / 'gmail_unread.lock'
PREVIOUS_COUNT_FILE = Path.home() / '.cache' / 'gmail_previous_count.txt'

def get_cached_data():
    """Get cached data if still valid"""
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
            cache_time = cache_data.get('timestamp', 0)
            current_time = time.time()

            # Check if cache is still valid
            if current_time - cache_time < CACHE_DURATION:
                return {
                    'count': cache_data.get('count', None),
                    'emails': cache_data.get('emails', [])
                }
    except Exception:
        pass

    return None

def get_cached_emails_only():
    """Get emails from cache even if expired (for preservation)"""
    if not CACHE_FILE.exists():
        return []
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
            return cache_data.get('emails', [])
    except Exception:
        return []

def save_cache(count, emails=None, preserve_existing=False):
    """Save unread count and emails to cache"""
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

        # If preserve_existing is True and emails is None, keep existing emails
        if preserve_existing and emails is None:
            # Read emails from cache file even if expired
            emails = get_cached_emails_only()

        cache_data = {
            'timestamp': time.time(),
            'count': count,
            'emails': emails or []
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception:
        pass

def get_previous_count():
    """Get the previous unread count"""
    try:
        if PREVIOUS_COUNT_FILE.exists():
            with open(PREVIOUS_COUNT_FILE, 'r') as f:
                return int(f.read().strip())
    except Exception:
        pass
    return None

def save_previous_count(count):
    """Save the current count as previous count"""
    try:
        PREVIOUS_COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PREVIOUS_COUNT_FILE, 'w') as f:
            f.write(str(count))
    except Exception:
        pass

def send_notification(title, message, urgency='normal'):
    """Send system notification using notify-send"""
    try:
        # Ensure proper encoding for notify-send
        # Use UTF-8 encoding and handle Unicode properly
        env = os.environ.copy()
        env['LC_ALL'] = 'en_US.UTF-8'
        env['LANG'] = 'en_US.UTF-8'

        subprocess.run([
            'notify-send',
            '-u', urgency,
            '-t', '10000',  # 10 seconds timeout
            '-i', 'mail-unread',  # Icon
            title,
            message
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    except Exception:
        pass

def notify_new_emails(current_count, previous_count, emails):
    """Send notifications for new emails"""
    if previous_count is None or current_count <= previous_count:
        return

    # Calculate how many new emails arrived
    new_count = current_count - previous_count

    if new_count <= 0:
        return

    # Get the newest emails (assuming they're the new ones)
    new_emails = emails[:new_count] if len(emails) >= new_count else emails

    if new_count == 1:
        # Single email notification
        email_info = new_emails[0]
        # Get sender name - preserve Unicode but limit length
        sender = email_info['sender']
        if not sender or sender.strip() == '':
            sender = "Unknown Sender"
        else:
            # Truncate if too long but keep Unicode
            sender = sender[:50]

        title = f"New email from {sender}"

        # Get subject - preserve Unicode but limit length
        subject = email_info['subject']
        if not subject or subject.strip() == '':
            subject = "(No Subject)"
        else:
            subject = subject[:100]

        send_notification(title, subject, 'normal')
    else:
        # Multiple emails notification
        title = f"{new_count} new emails"
        # Get sender names - preserve Unicode
        senders = []
        for e in new_emails[:3]:
            sender = e['sender']
            if sender and sender.strip():
                # Truncate but keep Unicode
                senders.append(sender[:30])
        if senders:
            message = f"From: {', '.join(senders)}"
        else:
            message = "New emails received"
        if new_count > 3:
            message += f" and {new_count - 3} more"
        send_notification(title, message, 'normal')

def get_unread_count():
    """Get unread email count from Gmail"""
    try:
        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)

        # Login
        mail.login(GMAIL_USER, GMAIL_PASSWORD)

        # Select inbox
        mail.select('INBOX')

        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')

        if status == 'OK':
            # Count unread emails - handle empty result properly
            if messages[0] and len(messages[0].strip()) > 0:
                # Split and count - filter out empty strings
                email_ids = [id for id in messages[0].split() if id]
                unread_count = len(email_ids)
            else:
                unread_count = 0
            mail.logout()
            return unread_count
        else:
            mail.logout()
            return 0

    except imaplib.IMAP4.error as e:
        print(f"IMAP Error: {e}", file=sys.stderr)
        return -1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return -1

def get_recent_emails(count=5):
    """Get recent emails with sender and subject"""
    try:
        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)

        # Login
        mail.login(GMAIL_USER, GMAIL_PASSWORD)

        # Select inbox
        mail.select('INBOX')

        # Search for all emails, sorted by date (newest first)
        status, messages = mail.search(None, 'ALL')

        if status != 'OK':
            mail.logout()
            return []

        # Get email IDs - filter out empty strings and convert to list
        email_ids = [id for id in messages[0].split() if id]

        # Get the most recent emails (last N)
        # IMAP returns oldest first, so take last N and reverse
        if len(email_ids) >= count:
            recent_ids = email_ids[-count:]
        else:
            recent_ids = email_ids
        recent_ids.reverse()  # Show newest first

        emails = []
        seen_subjects = set()  # Track to avoid duplicates
        for email_id in recent_ids:
            try:
                # Fetch email headers only (faster)
                status, msg_data = mail.fetch(email_id, '(RFC822.HEADER)')
                if status != 'OK' or not msg_data or not msg_data[0]:
                    continue

                # Parse email
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)

                # Get sender
                sender = email_message['From'] or 'Unknown'
                # Decode sender header if needed
                if sender:
                    decoded_sender = decode_header(sender)
                    if decoded_sender:
                        sender_parts = []
                        for part, encoding in decoded_sender:
                            if isinstance(part, bytes):
                                try:
                                    if encoding:
                                        sender_parts.append(part.decode(encoding))
                                    else:
                                        sender_parts.append(part.decode('utf-8', errors='ignore'))
                                except:
                                    sender_parts.append(part.decode('utf-8', errors='ignore'))
                            else:
                                sender_parts.append(part)
                        sender = ''.join(sender_parts)

                # Clean up sender (remove email address if present, keep name)
                if '<' in sender:
                    sender = sender.split('<')[0].strip().strip('"').strip("'")

                # Get subject
                subject = email_message['Subject'] or '(No Subject)'
                # Decode subject if needed
                decoded_subject = decode_header(subject)[0][0]
                if isinstance(decoded_subject, bytes):
                    subject = decoded_subject.decode('utf-8', errors='ignore')
                else:
                    subject = decoded_subject

                # Truncate if too long
                if len(subject) > 50:
                    subject = subject[:47] + '...'
                if len(sender) > 30:
                    sender = sender[:27] + '...'

                # Create unique key to avoid duplicates
                email_key = f"{sender}|{subject}"
                if email_key not in seen_subjects:
                    seen_subjects.add(email_key)
                    emails.append({
                        'sender': sender,
                        'subject': subject
                    })

                # Stop if we have enough unique emails
                if len(emails) >= count:
                    break
            except Exception as e:
                continue

        mail.logout()
        return emails

    except Exception as e:
        print(f"Error fetching emails: {e}", file=sys.stderr)
        return []

if __name__ == '__main__':
    if not GMAIL_USER or not GMAIL_PASSWORD:
        print("Error: GMAIL_USER and GMAIL_PASSWORD must be set", file=sys.stderr)
        print("0")
        sys.exit(1)

    # Check for command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else 'count'

    # Check cache first
    cached_data = get_cached_data()
    if cached_data is not None:
        cached_count = cached_data['count']
        cached_emails = cached_data.get('emails', [])

        # Check for notifications even with cached data
        previous_count = get_previous_count()
        if previous_count is not None and cached_count > previous_count:
            # New emails detected in cache - send notification
            notify_new_emails(cached_count, previous_count, cached_emails)
            save_previous_count(cached_count)
        elif previous_count is None:
            # First run - save current count as baseline
            save_previous_count(cached_count)

        # Output cached results
        if mode == 'count':
            print(cached_count)
        elif mode == 'emails':
            for email_info in cached_emails:
                print(f"{email_info['sender']}|{email_info['subject']}")
        sys.exit(0)

    # Check for lock file to prevent concurrent access
    if LOCK_FILE.exists():
        # Check if lock is stale (older than 30 seconds)
        lock_age = time.time() - LOCK_FILE.stat().st_mtime
        if lock_age < 30:
            # Lock exists and is fresh, use cached data if available
            cached_data = get_cached_data()
            if cached_data:
                if mode == 'count':
                    print(cached_data['count'])
                elif mode == 'emails':
                    emails = cached_data.get('emails', [])
                    for email_info in emails:
                        print(f"{email_info['sender']}|{email_info['subject']}")
                sys.exit(0)

    # Create lock file
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOCK_FILE.touch()
    except Exception:
        pass

    try:
        # Get previous count for notification comparison
        previous_count = get_previous_count()

        # Cache miss or expired - fetch from Gmail
        count = get_unread_count()

        # Always fetch emails to keep them fresh, but only when count is valid
        if count >= 0:
            if mode == 'emails':
                # Explicitly fetching emails - get fresh data
                emails = get_recent_emails(5)
                save_cache(count, emails)
            else:
                # Fetching count - also fetch emails to keep cache fresh
                # This ensures emails don't disappear
                emails = get_recent_emails(5)
                save_cache(count, emails)

            # Check for new emails and send notifications
            if previous_count is not None and count > previous_count:
                # Fetch emails if we don't have them yet
                if not emails:
                    emails = get_recent_emails(5)
                notify_new_emails(count, previous_count, emails)

            # Save current count as previous for next check
            save_previous_count(count)

        # Output results
        if mode == 'count':
            print(count)
        elif mode == 'emails':
            for email_info in emails:
                print(f"{email_info['sender']}|{email_info['subject']}")
    finally:
        # Remove lock file
        try:
            if LOCK_FILE.exists():
                LOCK_FILE.unlink()
        except Exception:
            pass
