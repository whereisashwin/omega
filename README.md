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

## How it runs
- A recurring scheduled job checks every ~3 hours while this session is alive.
- New alerts are appended to `australia-watch-log.md` (the memory of what's
  already been sent, so you never get the same alert twice).
- Notifications reach your phone only if **Remote Control** is connected; either
  way they show in the terminal.

## Limits (worth knowing)
- This runs inside an ephemeral cloud session. It works while the session is
  alive; a recurring schedule auto-expires after 7 days. Ping me to re-arm it.
- Reddit's API is firewalled here, so signal comes from web search across
  Australian news + Reddit discussion rather than the raw subreddit feed.
