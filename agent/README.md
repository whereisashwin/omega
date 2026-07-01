# Claude Code on your droplet, wired to all your MCPs

Install the real Claude Code agent on a server you control, connect your MCP
servers (Gmail, Drive, GitHub, …), and use it from anywhere via SSH. This gives
you a persistent, always-available agent that can act via email/Drive/GitHub —
not a one-shot chat session that disappears.

## The pieces

1. **Claude Code** (the CLI agent) installed globally on the droplet.
2. **Auth** — an Anthropic API key (or a Claude subscription login).
3. **MCP servers** registered at *user scope* so they're available in every
   session: Gmail + Drive (Google Workspace), GitHub, and any others you add.
4. **You**, connecting over SSH (use `tmux` so sessions survive disconnects).

## Install (run on the droplet)

```bash
# copy this folder to the droplet, e.g.:
#   scp -r agent root@YOUR_DROPLET:/opt/claude-setup
cd /opt/claude-setup

# 1. install Node + Claude Code (+ tmux, uv)
sudo bash setup.sh

# 2. add your secrets
cp env.example ~/.claude-mcp.env && nano ~/.claude-mcp.env   # fill in keys

# 3. register your MCP servers (reads ~/.claude-mcp.env)
bash setup-mcp.sh

# 4. sanity check
claude mcp list
```

## Auth

Two options, pick one:

- **API key (simplest for a server):** put `ANTHROPIC_API_KEY=sk-ant-...` in your
  shell profile (`~/.bashrc`) or `~/.claude-mcp.env`. Pay-per-token.
- **Subscription login:** run `claude` once and follow the login prompt. On a
  headless box you may need to complete the browser step on your laptop and paste
  the token back; API key is less hassle for a server.

## Using it

```bash
ssh you@YOUR_DROPLET
tmux new -s claude        # persistent session that survives disconnect
claude                    # start the agent; all your MCP tools are available
# ... later, reconnect:
ssh you@YOUR_DROPLET
tmux attach -t claude
```

Ask it things like *"summarize my unread emails and draft replies"* or
*"find the contract in Drive and tell me the renewal date."* It has the tools
because the MCP servers are registered.

### Non-interactive / scheduled runs

For unattended jobs (e.g. a nightly inbox digest), use print mode in cron:

```bash
claude -p "Summarize today's unread emails, create draft replies where needed." \
  --allowedTools "mcp__google__*" >> ~/claude-digest.log 2>&1
```

## Security model (important — read before granting Gmail/GitHub)

- Anything the agent reads (email, issues, docs) is **attacker-controllable** and
  can attempt prompt injection. Grant the **least** scope that works:
  - Google: `gmail.readonly` + `gmail.compose` + `drive.readonly` (compose lets it
    **draft**, not send). Add `gmail.send` only once you trust it.
  - GitHub: a fine-grained PAT limited to the repos you actually want it touching.
- Run Claude as a **normal user**, never root, and **not** as the user that owns
  your web root, so a bad instruction can't touch the site serving ashwingoyal.com.
  Ideally a **separate droplet** from the one running the website.
- Consider `--permission-mode default` (asks before actions) rather than
  auto-accept, at least until you've built trust.
- Tokens live in `~/.claude-mcp.env` (`chmod 600`) and Claude's own config; revoke
  anytime at https://myaccount.google.com/permissions and in the Anthropic console.

## Remove

```bash
bash uninstall.sh
```
