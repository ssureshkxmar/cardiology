#!/bin/bash

echo "========================================"
echo "  Cardiac AI Backend Server Launcher"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[1/4] Checking Python installation..."
python3 --version

echo
echo "[2/4] Checking if virtual environment exists..."
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "Virtual environment created successfully!"
fi

echo
echo "[3/4] Activating virtual environment..."
source venv/bin/activate

echo
echo "[4/4] Installing/Updating dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo
echo "========================================"
echo "  Starting Backend Server..."
echo "========================================"
echo
echo "Server will be available at:"
echo "  http://localhost:8000"
echo
echo "Press Ctrl+C to stop the server"
echo

python3 main.py
