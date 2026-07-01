#!/usr/bin/env bash
# Remove the Claude email/Drive agent completely.  sudo bash uninstall.sh
set -euo pipefail

echo "==> Stopping and disabling units"
systemctl stop claude-agent.timer 2>/dev/null || true
systemctl disable claude-agent.timer 2>/dev/null || true
systemctl stop claude-agent.service 2>/dev/null || true

echo "==> Removing systemd units"
rm -f /etc/systemd/system/claude-agent.timer /etc/systemd/system/claude-agent.service
systemctl daemon-reload

echo "==> Removing app files"
rm -rf /opt/claude-agent

read -r -p "Also delete secrets in /etc/claude-agent? [y/N] " ans
if [[ "${ans:-N}" =~ ^[Yy]$ ]]; then
  rm -rf /etc/claude-agent
  echo "    secrets removed."
fi

read -r -p "Also delete the 'claudeagent' user? [y/N] " ans2
if [[ "${ans2:-N}" =~ ^[Yy]$ ]]; then
  userdel -r claudeagent 2>/dev/null || true
  echo "    user removed."
fi

echo "==> Done. Remember to revoke the OAuth grant at"
echo "    https://myaccount.google.com/permissions  and the API key in the Anthropic console."
