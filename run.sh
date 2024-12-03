#!/bin/sh

# Ensure the required log files exist
touch /app/aria2.log /app/lazyleech.log

# Start logging in the background
tail -f /app/aria2.log &
tail -f /app/lazyleech.log &

# Start aria2 with updated options if applicable
aria2c --enable-rpc=true --rpc-listen-all=true --rpc-allow-origin-all -j5 -x5 > /app/aria2.log 2>&1 &

# Navigate to the app directory
cd /app || exit

# Run LazyLeech using the latest Python version available
python3 -m lazyleech > /app/lazyleech.log 2>&1
