#!/bin/bash

clear

echo "=========================="
echo "    Starting GeckoAI"
echo "=========================="

cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python3 start.py

echo
read -p "Press ENTER to exit..."