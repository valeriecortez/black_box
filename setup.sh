#!/bin/bash
# Setup script for Linux/Mac
# Installs all required dependencies

echo "========================================"
echo "  Installing Dependencies"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

echo "Installing Python packages..."
pip3 install -r requirements.txt

echo ""
echo "Installing Playwright browsers (optional, for JavaScript crawling)..."
echo "This may take a few minutes..."
playwright install chromium

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "To start the application, run: ./run.sh"
echo ""
