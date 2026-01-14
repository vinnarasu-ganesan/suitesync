#!/bin/bash

# SuiteSync Background Startup Script
# This script starts SuiteSync in the background using nohup

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting SuiteSync in background...${NC}"

# Check if already running
if [ -f "suitesync.pid" ]; then
    OLD_PID=$(cat suitesync.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}SuiteSync is already running with PID: $OLD_PID${NC}"
        echo "To stop it, run: ./stop_background.sh"
        exit 1
    else
        echo "Removing stale PID file..."
        rm suitesync.pid
    fi
fi

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${RED}Error: Virtual environment not found at .venv${NC}"
    echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source .venv/bin/activate

# Create logs directory
mkdir -p logs

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "The app will use default configuration"
fi

# Start gunicorn in background
echo "Starting Gunicorn with 4 workers..."
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app --timeout 120 > logs/suitesync.log 2>&1 &

# Get the PID
PID=$!

# Save PID to file
echo $PID > suitesync.pid

# Wait a moment to check if it started successfully
sleep 2

if ps -p $PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ SuiteSync started successfully!${NC}"
    echo ""
    echo "  PID: $PID"
    echo "  URL: http://localhost:5000"
    echo "  Logs: tail -f logs/suitesync.log"
    echo ""
    echo "To stop: ./stop_background.sh"
    echo "To view logs: ./view_logs.sh"
else
    echo -e "${RED}✗ Failed to start SuiteSync${NC}"
    echo "Check logs/suitesync.log for errors"
    rm suitesync.pid
    exit 1
fi

