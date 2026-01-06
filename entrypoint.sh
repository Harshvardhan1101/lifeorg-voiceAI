#!/bin/bash
set -e

echo "Initializing voice pipeline agent..."

# Download required model files first
python3 main.py download-files

# Start the agent in production mode
echo "Starting voice agent in production mode..."
exec python3 main.py start
