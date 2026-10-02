#!/usr/bin/env python3
"""
Gmail fetcher + notifier for the conky widget.

Run by a systemd user timer (gmail-fetch.timer). It is the ONLY process that
talks to Gmail or sends notifications. Conky reads the state file it writes
through gmail_render.py, which has no side effects.

Notifications are keyed on IMAP UIDs: a message is announced exactly once,
no matter how many times this runs, whether other mail gets read, archived or
deleted in between, or how many conky instances are displaying it.

State file: ~/.cache/conky_widget/gmail_state.json
Credentials: ~/.config/conky_widget/env (GMAIL_USER=..., GMAIL_PASSWORD=...)
"""

import email
import imaplib
import json
import os
import subprocess
import sys
import time
from email.header import decode_header, make_header
from pathlib import Path

ENV_FILE = Path.home() / ".config" / "conky_widget" / "env"
STATE_DIR = Path.home() / ".cache" / "conky_widget"
STATE_FILE = STATE_DIR / "gmail_state.json"
MAX_LISTED = 10          # unread messages kept in the state file (newest first)
MAX_SEEN = 2000          # seen UIDs kept (UIDs only grow, so pruning old ones is safe)
NOTIFY_SENDERS = 3       # senders named in a "N new emails" notification


def load_env():
    """Read KEY=value lines from the env file; environment variables win."""
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip().strip("'\"")
    for key in ("GMAIL_USER", "GMAIL_PASSWORD"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def read_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def write_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
    os.replace(tmp, STATE_FILE)   # atomic: readers never see a half-written file


def decode_hdr(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def clean_sender(raw):
    name, _, addr = raw.partition("<")
    name = name.strip().strip('"').strip("'")
    if name:
        return name
    return addr.strip("> ") or "Unknown sender"


def fetch_unread(user, password):
    """Return (uidvalidity, [ {uid, sender, subject, date} newest first ])."""
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    try:
        mail.login(user, password)
        mail.select("INBOX", readonly=True)
        uidvalidity = (mail.response("UIDVALIDITY")[1] or [b""])[0]
        uidvalidity = uidvalidity.decode() if uidvalidity else ""

        status, data = mail.uid("search", None, "UNSEEN")
        if status != "OK":
            raise RuntimeError("UID SEARCH failed")
        uids = sorted((int(u) for u in data[0].split()), reverse=True)

        messages = []
        for uid in uids[:MAX_LISTED]:
            status, parts = mail.uid(
                "fetch", str(uid), "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])"
            )
            if status != "OK" or not parts or not isinstance(parts[0], tuple):
                continue
            msg = email.message_from_bytes(parts[0][1])
            messages.append({
                "uid": uid,
                "sender": clean_sender(decode_hdr(msg.get("From", ""))),
                "subject": decode_hdr(msg.get("Subject", "")).strip() or "(No subject)",
                "date": msg.get("Date", ""),
            })
        return uidvalidity, uids, messages
    finally:
        try:
            mail.logout()
        except Exception:
            pass


def notify(title, body):
    env = dict(os.environ, LC_ALL="C.UTF-8")
    subprocess.run(
        ["notify-send", "-a", "Gmail", "-i", "mail-unread", "-u", "normal", title, body],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
    )


def announce(new_messages, new_count):
    if new_count == 1 and new_messages:
        m = new_messages[0]
        notify(f"New email from {m['sender'][:60]}", m["subject"][:120])
        return
    senders = []
    for m in new_messages[:NOTIFY_SENDERS]:
        if m["sender"] not in senders:
            senders.append(m["sender"][:30])
    body = "From: " + ", ".join(senders) if senders else "New mail received"
    if new_count > len(senders):
        body += f" and {new_count - len(senders)} more"
    notify(f"{new_count} new emails", body)


def main():
    creds = load_env()
    user, password = creds.get("GMAIL_USER"), creds.get("GMAIL_PASSWORD")
    if not user or not password:
        print(f"GMAIL_USER / GMAIL_PASSWORD missing (expected in {ENV_FILE})", file=sys.stderr)
        return 1

    state = read_state()
    try:
        uidvalidity, uids, messages = fetch_unread(user, password)
    except Exception as e:
        # Keep the last good data; the renderer shows it with an error marker.
        state["error"] = str(e)[:200]
        state["checked"] = time.time()
        write_state(state)
        print(f"Gmail fetch failed: {e}", file=sys.stderr)
        return 1

    seen = set(state.get("seen_uids", []))
    first_run = not state or state.get("uidvalidity") != uidvalidity
    if first_run:
        # Seed on first run (or mailbox UID reset): announce nothing.
        seen = set(uids)
    else:
        new_uids = [u for u in uids if u not in seen]
        if new_uids:
            new_msgs = [m for m in messages if m["uid"] in new_uids]
            announce(new_msgs, len(new_uids))
        seen.update(uids)

    # Prune old UIDs but never forget one that is still unread, or it would be re-announced.
    seen = sorted(set(sorted(seen, reverse=True)[:MAX_SEEN]) | set(uids), reverse=True)
    write_state({
        "updated": time.time(),
        "checked": time.time(),
        "uidvalidity": uidvalidity,
        "count": len(uids),
        "unread": messages,
        "seen_uids": seen,
        "error": None,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
