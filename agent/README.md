# Claude Email/Drive Agent — droplet deployment

A persistent agent that runs on your own server, reads your Gmail + Google Drive,
and **drafts** email replies on your behalf. It **never sends** — you review drafts
in Gmail and send them yourself. This is a deliberate v1 safety choice (see below).

## What it does

- Runs as an unprivileged systemd service on a timer (default: every 15 min).
- On each run it asks Claude (via the Agent SDK) to:
  - look at recent unread threads in your inbox,
  - read Drive files if a thread references one,
  - draft a reply as a **Gmail draft**.
- You get normal Gmail draft notifications; you review and send.

## The safety model (read this)

Email is attacker-controlled input. A malicious message can try to steer any agent
that reads it ("prompt injection"). This deployment mitigates that:

1. **No send tool.** The agent's allowed-tools list contains read + `create draft`
   only. The Gmail *send* tool is not granted, so injection cannot cause a send.
2. **Least privilege OS user.** Runs as `claudeagent`, no sudo, no access to your
   web root or the rest of the box. If the agent is ever compromised, blast radius
   is its own home dir.
3. **Read-only Google scopes recommended.** Use `gmail.readonly` + `drive.readonly`
   + `gmail.compose` (compose is needed to create drafts but does NOT allow sending
   existing mail). Do **not** grant `gmail.send` for v1.
4. **Secrets locked down.** API key + OAuth creds live in `/etc/claude-agent/env`,
   `chmod 600`, owned by `claudeagent`.
5. **Kill switch.** `sudo systemctl stop claude-agent.timer` halts it instantly;
   `uninstall.sh` removes it entirely.

> Strongly recommended: run this on a **separate droplet**, not the one serving
> ashwingoyal.com. If you must co-locate, the unprivileged-user isolation above is
> the minimum bar.

## What you provide (only you can do these)

1. **Anthropic API key** — from console.anthropic.com.
2. **Google OAuth client** — a Desktop OAuth client ID + secret with Gmail API and
   Drive API enabled, and yourself added as a test user. See the main chat for the
   Google Cloud console walkthrough.

## Install (run on the droplet as root)

```bash
# 1. copy this agent/ folder to the droplet, e.g. scp -r agent root@YOUR_DROPLET:/opt/claude-agent-src
# 2. on the droplet:
cd /opt/claude-agent-src
sudo bash setup.sh
# 3. fill in your secrets:
sudo nano /etc/claude-agent/env      # paste API key + Google client id/secret
# 4. one-time Google login (opens a device/URL auth flow, follow the printed link):
sudo -u claudeagent /opt/claude-agent/venv/bin/python /opt/claude-agent/run_agent.py --auth
# 5. start it:
sudo systemctl enable --now claude-agent.timer
```

## Watch it

```bash
systemctl status claude-agent.timer
journalctl -u claude-agent.service -f     # live logs of each run
```

## Kill / remove

```bash
sudo systemctl stop claude-agent.timer    # pause
sudo bash /opt/claude-agent-src/uninstall.sh   # remove everything
```

## Notes / things to verify on first run

- The MCP server used for Gmail/Drive is `workspace-mcp` (run via `uvx`). Tool names
  like `create_gmail_draft` / `search_gmail_messages` come from that server; if it
  updates and renames tools, adjust `ALLOWED_TOOLS` in `run_agent.py`.
- First run will be a no-op if there are no unread threads — that's expected.
- Tune cadence in `claude-agent.timer` (`OnUnitActiveSec`).
