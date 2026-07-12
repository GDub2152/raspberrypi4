#!/bin/bash
set -e
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
USER_NAME="${SUDO_USER:-$USER}"
HOME_DIR=$(getent passwd "$USER_NAME" | cut -d: -f6)
sudo apt update
sudo apt install -y python3-venv chromium unclutter
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
sudo tee /etc/systemd/system/sports-scoreboard.service >/dev/null <<EOF
[Unit]
Description=Pi Sports Scoreboard
After=network-online.target
Wants=network-online.target
[Service]
User=$USER_NAME
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/app.py
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now sports-scoreboard.service
mkdir -p "$HOME_DIR/.config/labwc"
touch "$HOME_DIR/.config/labwc/autostart"
grep -q 'sports-scoreboard-kiosk' "$HOME_DIR/.config/labwc/autostart" || cat >> "$HOME_DIR/.config/labwc/autostart" <<'EOF'
# sports-scoreboard-kiosk
sleep 8
unclutter -idle 1 &
chromium --kiosk --noerrdialogs --disable-infobars --no-first-run --disable-session-crashed-bubble http://127.0.0.1:8080 &
EOF
sudo chown -R "$USER_NAME:$USER_NAME" "$HOME_DIR/.config/labwc"
echo "Installed. Open http://$(hostname -I | awk '{print $1}'):8080/settings from another device. Reboot to launch kiosk."
