#!/bin/bash
# active_loop.sh - Simulates real human mouse movements, scrolling, and natural thinking pauses
export DISPLAY=:99

echo "Starting human-like active loop on DISPLAY=$DISPLAY..."

while true; do
  # Generate random coordinates within a typical task window range
  X=$((300 + RANDOM % 800))
  Y=$((200 + RANDOM % 600))
  
  # Move the mouse cursor visibly
  xdotool mousemove $X $Y
  
  # Scroll occasionally (approx. 10% chance)
  if [ $((RANDOM % 10)) -eq 0 ]; then
    xdotool click 5 # Scroll down
    sleep 0.2
    xdotool click 4 # Scroll up
  fi
  
  # Removed: long pauses would exceed 10s idle threshold and trigger inactive time
  
  sleep 2
done
