#!/usr/bin/env python3
"""Fever ticket checker: DroneArt Show Harry Potter, Sat 10 Oct 20:45,
Deluxe Stand, Admission for all ages. Pings Discord when >= 2 tickets are available."""
import os
import re
import sys
import time
from datetime import datetime

import requests

URL = "https://feverup.com/m/647897/en"
SESSION_ID = 478504514  # Sat 10 Oct 20:45 · Deluxe Stand · Admission for all ages
WANTED = int(os.getenv("WANTED", "2"))
INTERVAL = int(os.getenv("INTERVAL", "90"))  # seconds
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
MENTION = os.getenv("DISCORD_MENTION", "@everyone")  # or "<@your_user_id>"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

PATTERN = re.compile(
    r'"id":%d,"label":"([^"]+)".*?"starts_at_iso":"([^"]+)".*?'
    r'"available_tickets":(\d+),"has_available_tickets":(true|false)' % SESSION_ID,
    re.S,
)


def log(msg):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def check():
    # Cache-buster: the page is cached by CloudFront for up to 60s otherwise.
    r = requests.get(URL, params={"_": int(time.time())}, timeout=30, headers={
        "User-Agent": UA, "Accept-Language": "en", "Cache-Control": "no-cache"})
    r.raise_for_status()
    m = PATTERN.search(r.text)
    if not m:
        raise RuntimeError("session not found in page (sold out entirely or page changed)")
    return int(m.group(3))


def discord(content):
    if not WEBHOOK:
        log(f"(no DISCORD_WEBHOOK_URL set) would send: {content}")
        return
    r = requests.post(WEBHOOK, timeout=15, json={
        "content": content,
        "allowed_mentions": {"parse": ["everyone", "users", "roles"]},
    })
    r.raise_for_status()


def main():
    log(f"Watching session {SESSION_ID} every {INTERVAL}s (need {WANTED}).")
    discord(f"👀 Fever checker started: Deluxe Stand, Sat 10 Oct 20:45 — checking every {INTERVAL}s.")
    was_available = False
    while True:
        try:
            n = check()
            available = n >= WANTED
            if available and not was_available:
                log(f"✅ {n} AVAILABLE — pinging Discord")
                discord(f"{MENTION} 🎟 **{n} tickets available!** Deluxe Stand, Sat 10 Oct 20:45 "
                        f"(Admission for all ages)\n{URL}")
            elif not available and was_available:
                discord(f"❌ Gone again — now {n} available.")
            log(f"{n} available")
            was_available = available
        except Exception as e:
            log(f"⚠️  check failed: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    if "--once" in sys.argv:
        print(check())
    else:
        main()
