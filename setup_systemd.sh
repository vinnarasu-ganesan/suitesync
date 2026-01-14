#!/bin/bash

# SuiteSync Systemd Setup Script
# This script helps set up SuiteSync as a systemd service

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== SuiteSync Systemd Service Setup ===${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please do not run this script as root/sudo${NC}"
    echo "The script will prompt for sudo password when needed"
    exit 1
fi

# Get current directory
CURRENT_DIR="$(pwd)"
USER=$(whoami)

echo "Current directory: $CURRENT_DIR"
echo "Current user: $USER"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}Error: Virtual environment not found at .venv${NC}"
    echo "Please create it first: python3 -m venv .venv"
    exit 1
fi

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: app.py not found in current directory${NC}"
    echo "Please run this script from the SuiteSync root directory"
    exit 1
fi

echo -e "${YELLOW}This script will:${NC}"
echo "1. Update the systemd service file with current paths"
echo "2. Copy it to /etc/systemd/system/"
echo "3. Enable and start the service"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted"
    exit 0
fi

# Create logs directory
mkdir -p logs

# Create temporary service file with updated paths
TMP_SERVICE="/tmp/suitesync.service"

cat > "$TMP_SERVICE" << EOF
[Unit]
Description=SuiteSync - Test Synchronization Service
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$CURRENT_DIR"

ExecStart=$CURRENT_DIR/.venv/bin/gunicorn \\
    -w 4 \\
    -b 0.0.0.0:5000 \\
    --timeout 120 \\
    --access-logfile $CURRENT_DIR/logs/access.log \\
    --error-logfile $CURRENT_DIR/logs/error.log \\
    app:app

Restart=always
RestartSec=10

StandardOutput=append:$CURRENT_DIR/logs/suitesync.log
StandardError=append:$CURRENT_DIR/logs/suitesync-error.log

NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Created service file with current paths${NC}"

# Copy to system location
echo "Copying service file to /etc/systemd/system/ (requires sudo)..."
sudo cp "$TMP_SERVICE" /etc/systemd/system/suitesync.service

echo -e "${GREEN}✓ Service file installed${NC}"

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo -e "${GREEN}✓ Systemd reloaded${NC}"

# Enable service
echo "Enabling service to start on boot..."
sudo systemctl enable suitesync

echo -e "${GREEN}✓ Service enabled${NC}"

# Start service
echo "Starting service..."
sudo systemctl start suitesync

echo -e "${GREEN}✓ Service started${NC}"

# Wait a moment for startup
sleep 2

# Check status
echo ""
echo -e "${BLUE}=== Service Status ===${NC}"
sudo systemctl status suitesync --no-pager || true

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start suitesync"
echo "  Stop:    sudo systemctl stop suitesync"
echo "  Restart: sudo systemctl restart suitesync"
echo "  Status:  sudo systemctl status suitesync"
echo "  Logs:    sudo journalctl -u suitesync -f"
echo ""
echo "Access the application at: http://localhost:5000"

