#!/bin/bash
# SuiteSync Startup Script for Linux/Mac

echo "============================================================"
echo "  SuiteSync - Test Management Application"
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ ! -f ".venv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run: python3 -m venv .venv"
    echo "Then install requirements: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "Please edit .env file with your configuration."
    echo "Press any key to continue anyway..."
    read -n 1
fi

echo ""
echo "Starting SuiteSync application..."
echo ""
echo "Application will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the application"
echo ""
echo "============================================================"
echo ""

# Start the application
python app.py

