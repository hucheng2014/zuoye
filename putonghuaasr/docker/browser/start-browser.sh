#!/bin/bash
set -e

DISPLAY="${DISPLAY:-:99}"
DISPLAY_NUM="${DISPLAY#:}"
DISPLAY_NUM="${DISPLAY_NUM%%.*}"
echo "[browser] Cleaning stale X/Chromium locks for display ${DISPLAY}"
rm -f "/tmp/.X${DISPLAY_NUM}-lock" "/tmp/.X11-unix/X${DISPLAY_NUM}" \
  /home/pwuser/chrome-profile/SingletonLock \
  /home/pwuser/chrome-profile/SingletonSocket \
  /home/pwuser/chrome-profile/SingletonCookie
mkdir -p /tmp/.X11-unix

echo "[browser] Starting Xvfb on display ${DISPLAY} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})"
Xvfb "${DISPLAY}" -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}" -ac +extension GLX +render -noreset &
XVFB_PID=$!
sleep 1
if ! kill -0 "${XVFB_PID}" 2>/dev/null; then
    echo "[browser] ERROR: Xvfb failed to start on ${DISPLAY}"
    exit 1
fi

echo "[browser] Starting fluxbox window manager"
fluxbox &
sleep 1

echo "[browser] Starting Chromium with CDP on port ${CDP_PORT}"

# Find Playwright's Chromium binary
CHROME_BIN=$(find /ms-playwright -name "chrome" -path "*/chrome-linux/*" | head -1)
if [ -z "$CHROME_BIN" ]; then
    echo "[browser] ERROR: Cannot find Chromium binary in /ms-playwright"
    exit 1
fi
echo "[browser] Using: $CHROME_BIN"

"$CHROME_BIN" \
    --remote-debugging-port=${CDP_PORT} \
    --remote-debugging-address=0.0.0.0 \
    --remote-allow-origins=* \
    --user-data-dir=/home/pwuser/chrome-profile \
    --no-first-run \
    --disable-sync \
    --disable-default-apps \
    --no-default-browser-check \
    --disable-gpu \
    --disable-dev-shm-usage \
    --no-sandbox \
    --disable-blink-features=AutomationControlled \
    --disable-features=IsolateOrigins,site-per-process \
    --disable-infobars \
    --load-extension=/home/pwuser/stealth-extension \
    --window-size=${SCREEN_WIDTH},${SCREEN_HEIGHT} \
    --start-maximized \
    "https://sonic.jd.com/#/annotation/dataset/annotate" &
sleep 3

# Chromium binds CDP to 127.0.0.1 only and rejects non-localhost Host headers.
# Use socat to forward external connections to localhost (WebSocket works fine through socat).
# The agent must use Host: localhost header for HTTP requests.
CDP_EXTERNAL_PORT=$((CDP_PORT + 1))
echo "[browser] Starting socat CDP proxy: 0.0.0.0:${CDP_EXTERNAL_PORT} -> 127.0.0.1:${CDP_PORT}"
socat TCP-LISTEN:${CDP_EXTERNAL_PORT},fork,reuseaddr,bind=0.0.0.0 TCP:127.0.0.1:${CDP_PORT} &

echo "[browser] Starting x11vnc on port 5900"
VNC_ARGS="-display ${DISPLAY} -forever -shared -rfbport 5900 -noxdamage"
if [ -n "$VNC_PASSWORD" ]; then
    mkdir -p /home/pwuser/.vnc
    x11vnc -storepasswd "$VNC_PASSWORD" /home/pwuser/.vnc/passwd
    VNC_ARGS="$VNC_ARGS -rfbauth /home/pwuser/.vnc/passwd"
else
    VNC_ARGS="$VNC_ARGS -nopw"
fi
x11vnc $VNC_ARGS &
sleep 1

echo "[browser] Starting noVNC websockify on port 6080"
echo "[browser] Access browser at http://localhost:6080/vnc.html"

# websockify runs in foreground to keep container alive
exec websockify --web /usr/share/novnc 6080 localhost:5900
