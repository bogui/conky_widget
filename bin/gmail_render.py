#!/usr/bin/env python3
"""
Render the Gmail state file for conky. No network, no side effects.

  gmail_render.py count      -> "4"  (or "?" when the last fetch failed and nothing is cached)
  gmail_render.py list [N]   -> N unread messages as conky markup, newest first (default 4)
"""

import json
import sys
import time
from pathlib import Path

STATE_FILE = Path.home() / ".cache" / "conky_widget" / "gmail_state.json"
STALE_AFTER = 15 * 60       # seconds without a successful fetch before we flag it
SENDER_CHARS = 34
SUBJECT_CHARS = 48

C_SENDER = "${color #E0E0E0}"
C_SUBJECT = "${color #B0B0B0}"
C_WARN = "${color #FB9905}"
C_END = "${color}"


def conky_escape(text):
    """Make arbitrary text safe inside conky markup."""
    text = text.replace("$", "$$")           # ${...} and $var must not be parsed
    text = text.replace("\n", " ").replace("\r", " ")
    if text.startswith("#"):                 # a leading '#' would be a comment line
        text = " " + text
    return text


def shorten(text, limit):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def load():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "count"
    state = load()

    if mode == "count":
        if not state or state.get("count") is None:
            print("?")
        else:
            stale = time.time() - state.get("updated", 0) > STALE_AFTER
            print(f"{state['count']}{'!' if stale or state.get('error') else ''}")
        return 0

    if mode == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 4
        if not state:
            print(f"{C_WARN}waiting for first fetch…{C_END}")
            return 0
        unread = state.get("unread", [])[:limit]
        if state.get("error") and not unread:
            print(f"{C_WARN}fetch failed: {conky_escape(shorten(state['error'], 40))}{C_END}")
            return 0
        if not unread:
            print(f"{C_SUBJECT}No unread mail{C_END}")
            return 0
        for m in unread:
            sender = conky_escape(shorten(m.get("sender", ""), SENDER_CHARS))
            subject = conky_escape(shorten(m.get("subject", ""), SUBJECT_CHARS))
            print(f"{C_SENDER}{sender}{C_END}")
            print(f"{C_SUBJECT}  {subject}{C_END}")
        return 0

    print(f"unknown mode {mode}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
