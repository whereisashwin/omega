#!/usr/bin/env python3
"""Dingo Dispatch — Australian Reddit POV watcher.

Pulls the top *discussion & self-posts* from Australian subreddits and pushes
the most interesting ones to Telegram. Tuned for POV/human content — personal
stories, spicy takes, funny/weird/wholesome — and deliberately biased AWAY from
dry news-link posts.

No third-party dependencies (stdlib only) so it runs anywhere with python3.
Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment; if either
is missing it does nothing (so the workflow is a safe no-op until you add the
secrets).
"""
import base64
import html
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# POV-heavy Australian communities. Discussion + self-posts live here, not the
# news wire. Tune this list to taste.
SUBREDDITS = ["australia", "AskAnAustralian", "straya"]
# Reddit sorting: top posts of the day (community-vetted "interesting").
LISTING = "top"
TIME = "day"

STATE_PATH = Path(__file__).resolve().parent.parent / "state" / "seen.json"
# Reddit wants a descriptive User-Agent; generic browser UAs get rate-limited.
UA = "omega-dingo-dispatch/1.0 (Australian POV watcher; contact via github whereisashwin/omega)"

FETCH_LIMIT = 25          # how many top posts to consider per subreddit
MAX_PER_RUN = 3           # never fire more than this per run (detox-friendly)
MIN_SCORE = 80            # skip low-signal posts
MIN_COMMENTS = 25         # a real discussion needs real comments
SNIPPET_CHARS = 240       # how much of a self-post body to preview
STATE_LIMIT = 800         # cap remembered IDs so state file stays small

# Link posts pointing at these are "news" — the exact thing the user is sick of.
# Self-posts (domain "self.<sub>") are always kept; these only filter link posts.
NEWS_DOMAINS = (
    "abc.net.au", "news.com.au", "theguardian.com", "smh.com.au", "theage.com.au",
    "9news.com.au", "7news.com.au", "skynews.com.au", "sbs.com.au", "afr.com",
    "theconversation.com", "reuters.com", "dailymail.co.uk", "brisbanetimes.com.au",
    "watoday.com.au", "msn.com", "yahoo.com", "news.google.com", "crikey.com.au",
    "canberratimes.com.au", "theaustralian.com.au", "nine.com.au", "perthnow.com.au",
)


def reddit_token():
    """Get an app-only OAuth token. Reddit blocks anonymous datacenter IPs
    (GitHub Actions gets HTTP 403), so authenticated access is required."""
    cid = os.environ.get("REDDIT_CLIENT_ID")
    secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not cid or not secret:
        return None
    auth = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        headers={"Authorization": f"Basic {auth}", "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read()).get("access_token")


def fetch_listing(sub, token):
    """Fetch a subreddit's top-of-day listing via the authenticated API."""
    url = f"https://oauth.reddit.com/r/{sub}/{LISTING}?t={TIME}&limit={FETCH_LIMIT}&raw_json=1"
    req = urllib.request.Request(
        url, headers={"Authorization": f"bearer {token}", "User-Agent": UA}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def is_newsy(post):
    domain = (post.get("domain") or "").lower()
    return any(nd in domain for nd in NEWS_DOMAINS)


def interest_score(post):
    """Rank by discussion first (comments = POV/engagement), then upvotes.
    Self-posts get a bonus because they're the first-person content we want."""
    comments = post.get("num_comments", 0)
    ups = post.get("score", 0)
    self_bonus = 1.5 if post.get("is_self") else 1.0
    return (comments * 3 + ups) * self_bonus


def gather_candidates(token):
    posts = []
    for sub in SUBREDDITS:
        try:
            data = fetch_listing(sub, token)
        except Exception as exc:  # one bad sub shouldn't kill the run
            print(f"WARN: r/{sub} fetch failed: {exc}", file=sys.stderr)
            continue
        for child in data.get("data", {}).get("children", []):
            p = child.get("data", {})
            if p.get("stickied") or p.get("over_18") or p.get("pinned"):
                continue
            if p.get("score", 0) < MIN_SCORE or p.get("num_comments", 0) < MIN_COMMENTS:
                continue
            if not p.get("is_self") and is_newsy(p):  # drop news-link posts
                continue
            posts.append(p)
    posts.sort(key=interest_score, reverse=True)
    return posts


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
            "disable_web_page_preview": "true",
        }
    ).encode()
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status


def format_post(p):
    title = html.escape(p.get("title", "").strip())
    sub = p.get("subreddit", "")
    link = "https://www.reddit.com" + p.get("permalink", "")
    body = f"🐕 <b>Dingo Dispatch</b> 🇦🇺\n\n<b>{title}</b>"

    selftext = (p.get("selftext") or "").strip()
    if selftext:
        snippet = selftext[:SNIPPET_CHARS].strip()
        if len(selftext) > SNIPPET_CHARS:
            snippet += "…"
        body += f"\n\n{html.escape(snippet)}"
    elif not p.get("is_self"):
        # Link/image/video post — note where it points so context isn't lost.
        dest = (p.get("url") or "").strip()
        if dest and "reddit.com" not in dest:
            body += f"\n\n🔗 {html.escape(dest)}"

    body += (
        f"\n\n<i>r/{html.escape(sub)} · 👍 {p.get('score', 0)} · "
        f"💬 {p.get('num_comments', 0)}</i>\n{html.escape(link)}"
    )
    return body


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

    try:
        token = reddit_token()
    except Exception as exc:
        print(f"ERROR: Reddit auth failed: {exc}", file=sys.stderr)
        return 0
    if not token:
        print("No Reddit API creds set (REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET) "
              "— add them to enable the Reddit feed. Safe no-op.")
        return 0

    state = load_state()
    seen = set(state.get("seen", []))

    fresh = [p for p in gather_candidates(token) if p.get("id") not in seen]
    if not fresh:
        print("Nothing new & interesting right now.")
        return 0

    sent_keys = []
    for p in fresh[:MAX_PER_RUN]:
        try:
            telegram_send(token, chat_id, format_post(p))
            sent_keys.append(p["id"])
            print(f"Sent: r/{p.get('subreddit')} — {p.get('title')[:60]}")
        except Exception as exc:
            print(f"ERROR sending {p.get('id')}: {exc}", file=sys.stderr)

    # Only remember what we actually delivered, so a send failure retries later.
    state["seen"] = state.get("seen", []) + sent_keys
    save_state(state)
    print(f"Done. Sent {len(sent_keys)} interesting post(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
