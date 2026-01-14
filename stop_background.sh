#!/bin/bash

# SuiteSync Background Stop Script
# This script stops the background SuiteSync process

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping SuiteSync...${NC}"

# Check if PID file exists
if [ ! -f "suitesync.pid" ]; then
    echo -e "${RED}No PID file found. Is SuiteSync running?${NC}"

    # Try to find gunicorn processes anyway
    PIDS=$(pgrep -f "gunicorn.*app:app" || true)
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}Found gunicorn processes:${NC}"
        ps aux | grep "gunicorn.*app:app" | grep -v grep
        echo ""
        read -p "Kill these processes? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo $PIDS | xargs kill
            echo -e "${GREEN}✓ Processes killed${NC}"
        fi
    else
        echo "No gunicorn processes found"
    fi
    exit 0
fi

# Read PID from file
PID=$(cat suitesync.pid)

# Check if process is running
if ps -p $PID > /dev/null 2>&1; then
    echo "Stopping SuiteSync (PID: $PID)..."

    # Try graceful shutdown first
    kill $PID

    # Wait up to 10 seconds for graceful shutdown
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓ SuiteSync stopped gracefully${NC}"
            rm suitesync.pid
            exit 0
        fi
        sleep 1
    done

    # Force kill if still running
    echo "Process didn't stop gracefully, force killing..."
    kill -9 $PID 2>/dev/null || true

    if ! ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ SuiteSync force stopped${NC}"
        rm suitesync.pid
    else
        echo -e "${RED}✗ Failed to stop SuiteSync${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Process with PID $PID is not running${NC}"
    echo "Removing stale PID file..."
    rm suitesync.pid
fi

# Also kill any remaining gunicorn worker processes
WORKER_PIDS=$(pgrep -f "gunicorn.*app:app" || true)
if [ -n "$WORKER_PIDS" ]; then
    echo "Cleaning up worker processes..."
    echo $WORKER_PIDS | xargs kill 2>/dev/null || true
    sleep 1

    # Force kill if still there
    WORKER_PIDS=$(pgrep -f "gunicorn.*app:app" || true)
    if [ -n "$WORKER_PIDS" ]; then
        echo $WORKER_PIDS | xargs kill -9 2>/dev/null || true
    fi
fi

echo -e "${GREEN}✓ All SuiteSync processes stopped${NC}"

