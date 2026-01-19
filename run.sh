#!/bin/bash
# Advanced Web Crawler Launcher
# This script starts the Streamlit application

echo "========================================"
echo "  Advanced Web Crawler & Backlink Analyzer"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

echo "Starting application..."
echo ""
echo "The application will open in your default browser."
echo "Press Ctrl+C to stop the server."
echo ""

# Start Streamlit
streamlit run app.py
