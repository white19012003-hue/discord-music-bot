#!/bin/bash
# Start script for Discord Music Bot on Render

echo "Starting Discord Music Bot..."

# Install dependencies if needed
pip install -r requirements.txt

# Run the bot
python bot.py
