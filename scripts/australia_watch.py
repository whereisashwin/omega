#!/usr/bin/env python3
"""Australia news watcher.

Fetches Australia's news front page, finds genuinely-new front-page stories
since the last run, and pushes them to Telegram. Designed to be detox-friendly:
it only sends *new* top-of-front-page items, capped per run, so you get the
signal without the firehose.

No third-party dependencies (stdlib only) so it runs anywhere with python3.
Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment; if either
is missing it does nothing (so the workflow is a safe no-op until you add the
secrets).
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

# Australia (AU edition) Google News front page — reliable, no API key, already
# ranked by importance. Add more feeds here and they get merged + deduped.
FEEDS = [
    "https://news.google.com/rss?hl=en-AU&gl=AU&ceid=AU:en",
]

STATE_PATH = Path(__file__).resolve().parent.parent / "state" / "seen.json"
UA = "Mozilla/5.0 (compatible; omega-australia-watch/1.0)"

# Only look at the top N items of each feed (the actual front page) and never
# push more than MAX_PER_RUN at once — keeps it to real headlines, not a flood.
TOP_N = 8
MAX_PER_RUN = 3
# Cap remembered IDs so state/seen.json doesn't grow forever.
STATE_LIMIT = 500


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def parse_items(xml_bytes):
    """Return [(item_id, title, link), ...] from an RSS feed."""
    items = []
    root = ET.fromstring(xml_bytes)
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        if not title:
            continue
        items.append((guid, html.unescape(title), link))
    return items


def load_state():
    try:
        return json.loads(STATE_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"seen": []}


def save_state(state):
    state["seen"] = state["seen"][-STATE_LIMIT:]
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def telegram_send(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "false",
        }
    ).encode()
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("No Telegram secrets set — nothing to do (safe no-op).")
        return 0

    # Curated path: if a message was passed in (e.g. by the smart in-session
    # cron via workflow_dispatch), just deliver it verbatim and stop.
    message = os.environ.get("WATCH_MESSAGE", "").strip()
    if message:
        telegram_send(token, chat_id, message)
        print("Sent curated message.")
        return 0

    state = load_state()
    seen = set(state.get("seen", []))

    # Gather candidates from the top of each feed.
    candidates = []
    for feed in FEEDS:
        try:
            for item_id, title, link in parse_items(fetch(feed))[:TOP_N]:
                candidates.append((item_id, title, link))
        except Exception as exc:  # one bad feed shouldn't kill the run
            print(f"WARN: feed failed {feed}: {exc}", file=sys.stderr)

    # Keep order, drop already-seen and in-run duplicates.
    fresh = []
    batch_seen = set()
    for item_id, title, link in candidates:
        key = item_id or link
        if key in seen or key in batch_seen:
            continue
        batch_seen.add(key)
        fresh.append((key, title, link))

    if not fresh:
        print("Nothing new on the front page.")
        return 0

    to_send = fresh[:MAX_PER_RUN]
    sent_keys = []
    for key, title, link in to_send:
        # Google News titles are "Headline - Source"; split the source out.
        m = re.match(r"^(.*) - ([^-]+)$", title)
        headline, source = (m.group(1), m.group(2)) if m else (title, "")
        body = f"🇦🇺 <b>{html.escape(headline)}</b>"
        if source:
            body += f"\n<i>{html.escape(source.strip())}</i>"
        if link:
            body += f"\n{html.escape(link)}"
        try:
            telegram_send(token, chat_id, body)
            sent_keys.append(key)
            print(f"Sent: {headline}")
        except Exception as exc:
            print(f"ERROR sending '{headline}': {exc}", file=sys.stderr)

    # Only remember what we actually delivered, so a send failure retries later.
    state["seen"] = state.get("seen", []) + sent_keys
    save_state(state)
    print(f"Done. Sent {len(sent_keys)} new item(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
