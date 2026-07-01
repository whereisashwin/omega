#!/usr/bin/env bash
# Hardened installer for the Claude email/Drive agent.
# Run as root on the droplet:  sudo bash setup.sh
set -euo pipefail

APP_USER=claudeagent
APP_HOME=/opt/claude-agent
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR=/etc/claude-agent

echo "==> Creating unprivileged user '$APP_USER' (no sudo, no login shell)"
if ! id "$APP_USER" &>/dev/null; then
  useradd --system --create-home --home-dir "$APP_HOME" --shell /usr/sbin/nologin "$APP_USER"
fi

echo "==> Installing OS deps (python3, venv, pipx/uv for the MCP server)"
if command -v apt-get &>/dev/null; then
  apt-get update -y
  apt-get install -y python3 python3-venv python3-pip curl
fi

echo "==> Installing 'uv' (for uvx-launched MCP server) for $APP_USER"
if ! sudo -u "$APP_USER" bash -lc 'command -v uv' &>/dev/null; then
  sudo -u "$APP_USER" bash -lc 'curl -LsSf https://astral.sh/uv/install.sh | sh'
fi

echo "==> Creating Python venv and installing the Agent SDK"
sudo -u "$APP_USER" python3 -m venv "$APP_HOME/venv"
sudo -u "$APP_USER" "$APP_HOME/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_HOME/venv/bin/pip" install -r "$SRC_DIR/requirements.txt"

echo "==> Deploying agent code"
install -o "$APP_USER" -g "$APP_USER" -m 0644 "$SRC_DIR/run_agent.py" "$APP_HOME/run_agent.py"

echo "==> Creating secrets dir $ENV_DIR (locked to $APP_USER, chmod 600)"
mkdir -p "$ENV_DIR"
if [ ! -f "$ENV_DIR/env" ]; then
  install -o "$APP_USER" -g "$APP_USER" -m 0600 "$SRC_DIR/env.example" "$ENV_DIR/env"
  echo "    -> created $ENV_DIR/env FROM TEMPLATE. Edit it and add your real secrets."
else
  echo "    -> $ENV_DIR/env already exists, leaving it untouched."
fi
chmod 600 "$ENV_DIR/env"; chown "$APP_USER:$APP_USER" "$ENV_DIR/env"

echo "==> Installing systemd units"
install -m 0644 "$SRC_DIR/claude-agent.service" /etc/systemd/system/claude-agent.service
install -m 0644 "$SRC_DIR/claude-agent.timer" /etc/systemd/system/claude-agent.timer
systemctl daemon-reload

echo "==> Firewall reminder"
echo "    This agent makes only OUTBOUND https calls; it needs no inbound ports."
echo "    If you use ufw:  ufw default deny incoming; ufw allow OpenSSH; ufw enable"

cat <<EOF

==> Done. Next steps:
  1. Edit secrets:   sudo nano $ENV_DIR/env
  2. One-time login: sudo -u $APP_USER $APP_HOME/venv/bin/python $APP_HOME/run_agent.py --auth
  3. Start:          sudo systemctl enable --now claude-agent.timer
  4. Logs:           journalctl -u claude-agent.service -f
EOF
