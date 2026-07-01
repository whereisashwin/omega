#!/usr/bin/env bash
# Register MCP servers with Claude Code at USER scope (available in every session).
# Run as the NORMAL user who will use Claude (not root):  bash setup-mcp.sh
# Reads secrets from ~/.claude-mcp.env
set -euo pipefail

ENV_FILE="${CLAUDE_MCP_ENV:-$HOME/.claude-mcp.env}"
if [ ! -f "$ENV_FILE" ]; then
  echo "!! $ENV_FILE not found. Copy env.example there and fill it in first."
  exit 1
fi
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a
chmod 600 "$ENV_FILE" || true

echo "==> Google Workspace (Gmail + Drive) — draft/read only, no send scope"
if [ -n "${GOOGLE_OAUTH_CLIENT_ID:-}" ]; then
  claude mcp remove google 2>/dev/null || true
  claude mcp add google --scope user \
    --env GOOGLE_OAUTH_CLIENT_ID="$GOOGLE_OAUTH_CLIENT_ID" \
    --env GOOGLE_OAUTH_CLIENT_SECRET="$GOOGLE_OAUTH_CLIENT_SECRET" \
    --env GOOGLE_OAUTH_SCOPES="https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose https://www.googleapis.com/auth/drive.readonly" \
    -- uvx workspace-mcp --tools gmail drive
  echo "    added. First use will open a Google OAuth flow."
else
  echo "    skipped (no GOOGLE_OAUTH_CLIENT_ID in env)."
fi

echo "==> GitHub (hosted MCP server)"
if [ -n "${GITHUB_PAT:-}" ]; then
  claude mcp remove github 2>/dev/null || true
  claude mcp add github --scope user --transport http https://api.githubcopilot.com/mcp/ \
    --header "Authorization: Bearer $GITHUB_PAT"
  echo "    added."
else
  echo "    skipped (no GITHUB_PAT in env)."
fi

# ---- Add more MCP servers here as needed, e.g.: ----
# claude mcp add filesystem --scope user -- npx -y @modelcontextprotocol/server-filesystem "$HOME/work"
# claude mcp add slack --scope user --env SLACK_BOT_TOKEN=... -- npx -y @modelcontextprotocol/server-slack

echo
echo "==> Registered servers:"
claude mcp list
echo
echo "Tip: run 'claude' then '/mcp' to check connection + trigger any pending OAuth."
