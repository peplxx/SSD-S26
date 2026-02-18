#!/bin/bash

echo "==> Update hosts file to resolve localhost.localdomain to 127.0.0.1"
echo "127.0.0.1  localhost.localdomain" >> /etc/hosts

echo "==> Download stable labenv from github releases..."
wget -q https://github.com/sh3b0/interactive-labs/releases/download/boxes/labenv-stable.zip
unzip -q labenv-stable.zip -d /app && rm labenv-stable.zip

echo "==> Installing npm dependencies and building the app..."
cd /app && npm ci 2>/dev/null

echo "==> Fixing script permissions..."
chmod +x /app/scripts/*

echo "==> Installing startup service..."
cat <<EOF > /etc/systemd/system/startup.service
[Unit]
Description=Startup Script
After=multi-user.target network-online.target
Wants=network-online.target
ConditionPathExists=/app/scripts/cmd.sh

[Service]
Type=exec
ExecStart=/app/scripts/cmd.sh
RemainAfterExit=yes
StandardOutput=journal
WorkingDirectory=/app
User=ubuntu
Group=ubuntu
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable startup
systemctl start startup

echo "==> Running browser container..."
docker network create lab_net || true
docker pull -q jlesage/firefox:v26.01.1
docker run -p5800:5800 -d --network lab_net jlesage/firefox:v26.01.1

echo "==> Provisioning complete! Access labenv at http://localhost:3000 (if using port-forwarding)"
echo "==> Additional machine IPs: $(hostname -I)"
