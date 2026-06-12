#!/bin/bash
# Get the browser WebSocket URL from the browser container and output it
# This is meant to be run on the HOST, not inside a container
WS_URL=$(docker exec oneform-browser python3 -c "
import urllib.request, json
r = urllib.request.urlopen('http://localhost:9222/json/version')
d = json.loads(r.read())
print(d['webSocketDebuggerUrl'])
" 2>/dev/null)

# Replace localhost:9222 with browser:9223 for use from agent container
echo "$WS_URL" | sed 's|ws://localhost:9222|ws://browser:9223|'
