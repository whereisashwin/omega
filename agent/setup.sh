#!/usr/bin/env bash
# Install Claude Code + prerequisites on an Ubuntu/Debian droplet.
# Run as root:  sudo bash setup.sh
set -euo pipefail

echo "==> Installing base tools (curl, git, tmux)"
if command -v apt-get &>/dev/null; then
  apt-get update -y
  apt-get install -y curl git tmux ca-certificates
else
  echo "!! Non-apt distro: install curl, git, tmux manually, then re-run the Node/Claude steps."
fi

echo "==> Installing Node.js 20 LTS (via NodeSource)"
if ! command -v node &>/dev/null || [ "$(node -v | cut -c2-3)" -lt 18 ]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi
echo "    node $(node -v), npm $(npm -v)"

echo "==> Installing Claude Code globally"
npm install -g @anthropic-ai/claude-code
echo "    $(claude --version 2>/dev/null || echo 'claude installed')"

echo "==> Installing uv (used by some MCP servers, e.g. Google Workspace)"
if ! command -v uv &>/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

cat <<'EOF'

==> Done installing.
Next:
  1. cp env.example ~/.claude-mcp.env && nano ~/.claude-mcp.env   # add your keys
  2. bash setup-mcp.sh                                            # register MCP servers
  3. claude mcp list                                             # verify
  4. tmux new -s claude && claude                                # use it

Reminder: run `claude` as a NORMAL user, not root, and not as your web-server user.
EOF
