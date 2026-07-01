#!/usr/bin/env bash
# Remove Claude Code and its MCP registrations.  bash uninstall.sh
set -euo pipefail

echo "==> Removing MCP server registrations"
for s in google github filesystem slack; do
  claude mcp remove "$s" 2>/dev/null || true
done

echo "==> Uninstalling Claude Code"
npm uninstall -g @anthropic-ai/claude-code 2>/dev/null || true

echo "==> Leaving Node, tmux, and uv installed (remove manually if you want)."
echo "==> Your secrets file ~/.claude-mcp.env is NOT deleted; remove it yourself:"
echo "      rm -f ~/.claude-mcp.env"
echo
echo "==> Remember to revoke access you granted:"
echo "    Google:  https://myaccount.google.com/permissions"
echo "    GitHub:  https://github.com/settings/tokens"
echo "    Anthropic API key: console.anthropic.com"
