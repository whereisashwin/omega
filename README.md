# 🐕 Dingo Dispatch — Australia Reddit/News Watch

Delivered by the **Dingo Dispatch** Telegram bot ([@DingoDispatchBot](https://t.me/DingoDispatchBot)).

A digital-detox-friendly watch on Australian **Reddit POV content** — personal
stories, spicy takes, funny/weird/wholesome threads — so you can stay off Reddit
and still get the interesting stuff. It's tuned *away* from dry news headlines.

## What gets pinged (the good stuff)
- **Personal stories & POV:** "what's it like…", life-in-Australia experiences,
  first-person dilemmas, moments people share
- **Spicy takes & debates:** high-engagement discussion threads people are
  actually arguing about
- **Funny / weird / wholesome:** r/straya humour, only-in-Australia moments,
  wildlife chaos
- Ranked by real discussion (comments) + upvotes, self-posts favoured

## What gets ignored (no push)
- Dry news-link posts (the thing you're sick of), low-engagement posts
- Stickied megathreads, NSFW, duplicates of things already sent

## Sources
`r/australia`, `r/AskAnAustralian`, `r/straya` — top posts of the day. Edit
`SUBREDDITS` in `scripts/australia_watch.py` to add/remove communities.

## How it runs (two layers, both deliver to Telegram)
1. **Durable backbone — GitHub Action** (`.github/workflows/australia-watch.yml`).
   Runs every 3 hours on GitHub's servers, so it survives this cloud session
   ending. It pulls the top discussion/self-posts from the subreddits above,
   filters out news + noise, dedupes against `state/seen.json`, and sends the
   most interesting new ones to your Telegram.
2. **Smart layer — in-session cron.** While a Claude session is alive, it does
   LLM-judged curation for extra-interesting POV threads and delivers via the
   same workflow (`workflow_dispatch` with a curated `message`), so the bot
   token only ever lives as a GitHub secret.

New alerts are appended to `australia-watch-log.md` so you never get the same
alert twice.

## Telegram setup (one-time)
Bot is already created: **Dingo Dispatch** ([@DingoDispatchBot](https://t.me/DingoDispatchBot)).
Remaining steps:
1. Open [@DingoDispatchBot](https://t.me/DingoDispatchBot) and send it any
   message (e.g. "hi") so it's allowed to DM you.
2. Message **@userinfobot** → it replies with your numeric **chat id**.
3. In GitHub: **repo → Settings → Secrets and variables → Actions → New
   repository secret**, add two secrets:
   - `TELEGRAM_BOT_TOKEN` = the token @BotFather gave you
   - `TELEGRAM_CHAT_ID` = the id from step 2
4. Enable Actions if prompted (repo → Actions tab). Done — alerts start flowing.

> Security: the token is a password for your bot. Keep it only in the GitHub
> secret above — never commit it. To rotate it, send `/revoke` to @BotFather.

## Reddit API setup (one-time, ~2 min) — required for the good stuff
Reddit blocks anonymous datacenter IPs (GitHub Actions gets `HTTP 403`), so the
watcher reads Reddit through the **official API** with an app-only token. Free.
1. Go to <https://www.reddit.com/prefs/apps> → **create another app…**
2. Pick type **script**, name it anything (e.g. `dingo-dispatch`), set redirect
   URI to `http://localhost` (unused but required). Create it.
3. Copy the two values:
   - **client id** — the short string just under the app name ("personal use script")
   - **secret** — the longer `secret` field
4. Add them as GitHub repo secrets (same place as the Telegram ones):
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`

Without these the Action is a safe no-op (sends nothing). With them, it reads the
subreddits directly every 3 hours.

You can also run a check on demand: **Actions tab → Australia Watch → Run
workflow** (optionally type a custom message to send yourself).

## Limits (worth knowing)
- The GitHub Action keeps running on GitHub's infra. Scheduled workflows pause
  after ~60 days of zero repo activity — a single commit re-arms them.
- The in-session smart layer only runs while a Claude session is alive and
  auto-expires after 7 days; ping me to re-arm. The Action covers the gaps.
- Reddit blocks anonymous datacenter IPs, so the Action authenticates with the
  official Reddit API (see setup above). That's the one required key.
