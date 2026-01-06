#!/bin/bash
set -e

# Trap signals for graceful shutdown
trap 'echo "Received SIGTERM, shutting down gracefully..."; exit 0' SIGTERM
trap 'echo "Received SIGINT, shutting down gracefully..."; exit 0' SIGINT

echo "Initializing voice pipeline agent..."

# Download required model files first (including Silero VAD)
echo "Downloading model files..."
python3 main.py download-files || echo "Download-files completed (some files may already exist)"

# Pre-download Silero VAD model to avoid timeout during prewarm
echo "Pre-loading Silero VAD model..."
python3 -c "from livekit.plugins import silero; silero.VAD.load(); print('Silero VAD model loaded successfully')" || echo "Silero VAD pre-load skipped"

# Start the agent in production mode
echo "Starting voice agent in production mode..."
exec python3 main.py start
