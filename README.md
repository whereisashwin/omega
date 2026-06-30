# 🇦🇺 Australia Reddit/News Watch

A digital-detox-friendly watch on Australia-related Reddit and news. Claude polls
periodically, filters out the routine noise, and **only pushes a notification when
something genuinely important happens** — so you can stay off Reddit and still get
the dope.

## What counts as "important" (push-worthy)
- Breaking national news: politics, economy, disasters, safety/emergencies
- Major policy changes that affect daily life (tax, wages, rates, housing)
- Big, high-engagement r/australia threads that signal a real event (not memes)
- Anything most Australians would want to know *today*

## What gets ignored (no push)
- Routine discussion, memes, shitposts, recurring complaint threads
- Low-engagement posts, duplicates of things already alerted

## How it runs (two layers, both deliver to Telegram)
1. **Durable backbone — GitHub Action** (`.github/workflows/australia-watch.yml`).
   Runs every 3 hours on GitHub's servers, so it survives this cloud session
   ending. It pulls Australia's news front page, dedupes against
   `state/seen.json`, and sends new top-of-front-page items to your Telegram.
2. **Smart layer — in-session cron.** While a Claude session is alive, it does
   LLM-judged web-search filtering (catches Reddit-specific events the news feed
   misses) and delivers via the same workflow (`workflow_dispatch` with a
   curated `message`), so the bot token only ever lives as a GitHub secret.

New alerts are appended to `australia-watch-log.md` so you never get the same
alert twice.

## Telegram setup (one-time)
1. In Telegram, message **@BotFather** → `/newbot` → follow prompts → copy the
   **bot token** it gives you.
2. Send your new bot any message (say "hi") so it's allowed to message you.
3. Message **@userinfobot** → it replies with your numeric **chat id**.
4. In GitHub: **repo → Settings → Secrets and variables → Actions → New
   repository secret**, add two secrets:
   - `TELEGRAM_BOT_TOKEN` = the token from step 1
   - `TELEGRAM_CHAT_ID` = the id from step 3
5. Enable Actions if prompted (repo → Actions tab). Done — alerts start flowing.

You can also run a check on demand: **Actions tab → Australia Watch → Run
workflow** (optionally type a custom message to send yourself).

## Limits (worth knowing)
- The GitHub Action keeps running on GitHub's infra. Scheduled workflows pause
  after ~60 days of zero repo activity — a single commit re-arms them.
- The in-session smart layer only runs while a Claude session is alive and
  auto-expires after 7 days; ping me to re-arm. The Action covers the gaps.
- Reddit's API is firewalled in the Claude sandbox, so signal comes from web
  search / news front page rather than the raw subreddit feed.
