#!/usr/bin/env bash
set -euo pipefail

DISPLAY="${DISPLAY:-:99}"
DISPLAY_NUM="${DISPLAY#:}"
DISPLAY_NUM="${DISPLAY_NUM%%.*}"

# ────────────────────────────────────────────────────────────────
# 1. 清理陈旧锁文件 + Chrome profile 缓存（每次启动清理）
# ────────────────────────────────────────────────────────────────
echo "[browser] Cleaning stale locks for display ${DISPLAY}"
rm -f "/tmp/.X${DISPLAY_NUM}-lock" "/tmp/.X11-unix/X${DISPLAY_NUM}" \
  /home/pwuser/chrome-profile/SingletonLock \
  /home/pwuser/chrome-profile/SingletonSocket \
  /home/pwuser/chrome-profile/SingletonCookie
mkdir -p /tmp/.X11-unix

# 清理孤儿 Chromium IPC socket（在 /tmp 下积累的 .org.chromium.* 目录）
ORPHAN_COUNT=$(find /tmp -maxdepth 1 -name '.org.chromium.Chromium.*' -type d 2>/dev/null | wc -l)
if [ "$ORPHAN_COUNT" -gt 0 ]; then
  echo "[browser] Cleaning ${ORPHAN_COUNT} orphan Chromium IPC dirs in /tmp"
  find /tmp -maxdepth 1 -name '.org.chromium.Chromium.*' -type d -exec rm -rf {} + 2>/dev/null || true
fi

# 清理 Chrome profile 膨胀缓存（Service Worker, Cache, Code Cache 会随时间膨胀到 GB 级别）
PROFILE="/home/pwuser/chrome-profile/Default"
if [ -d "$PROFILE" ]; then
  for cache_dir in "Service Worker" "Cache/Cache_Data" "Code Cache" "GPUCache"; do
    if [ -d "$PROFILE/$cache_dir" ]; then
      SIZE=$(du -sm "$PROFILE/$cache_dir" 2>/dev/null | cut -f1)
      if [ "${SIZE:-0}" -gt 50 ]; then
        echo "[browser] Cleaning bloated cache: $cache_dir (${SIZE}MB)"
        rm -rf "$PROFILE/$cache_dir"
      fi
    fi
  done
fi

# ────────────────────────────────────────────────────────────────
# 2. 启动虚拟显示 + 窗口管理器
# ────────────────────────────────────────────────────────────────
echo "[browser] Starting Xvfb on display ${DISPLAY} (${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH})"
Xvfb "${DISPLAY}" -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}" \
  -ac +extension GLX +render -noreset &
XVFB_PID=$!
sleep 1
if ! kill -0 "${XVFB_PID}" 2>/dev/null; then
  echo "[browser] ERROR: Xvfb failed to start"
  exit 1
fi

echo "[browser] Starting fluxbox window manager"
fluxbox &
sleep 1

# ────────────────────────────────────────────────────────────────
# 3. 检测 shm 大小 → 决定是否使用 --disable-dev-shm-usage
# ────────────────────────────────────────────────────────────────
SHM_KB=$(df -k /dev/shm | tail -1 | awk '{print $2}')
SHM_MB=$((SHM_KB / 1024))
echo "[browser] /dev/shm size: ${SHM_MB}MB"

SHM_FLAGS=""
if [ "$SHM_MB" -lt 256 ]; then
  echo "[browser] WARNING: /dev/shm only ${SHM_MB}MB, using --disable-dev-shm-usage (slower!)"
  SHM_FLAGS="--disable-dev-shm-usage"
else
  echo "[browser] /dev/shm adequate (${SHM_MB}MB), Chrome IPC will use shared memory (fast)"
fi

# ────────────────────────────────────────────────────────────────
# 4. GPU 策略：使用 SwiftShader（Chrome 自带的 CPU 软件渲染）
#    不映射 /dev/dri — 避免容器内 Mesa 版本与宿主机不匹配导致崩溃
# ────────────────────────────────────────────────────────────────
GPU_FLAGS="--use-gl=swiftshader --disable-gpu-compositing --disable-software-rasterizer"
echo "[browser] GPU policy: SwiftShader (CPU software rendering, no /dev/dri needed)"

# ────────────────────────────────────────────────────────────────
# 5. 启动 Chrome（兼容 Playwright Chromium 和 Google Chrome）
# ────────────────────────────────────────────────────────────────
CHROME_BIN=""
# 优先 Google Chrome
if command -v google-chrome &>/dev/null; then
  CHROME_BIN="google-chrome"
elif command -v google-chrome-stable &>/dev/null; then
  CHROME_BIN="google-chrome-stable"
else
  # Playwright Chromium
  CHROME_BIN=$(find /ms-playwright -name chrome -path '*/chrome-linux/*' 2>/dev/null | head -1)
fi
if [ -z "$CHROME_BIN" ]; then
  echo "[browser] ERROR: Cannot find any Chrome/Chromium binary"
  exit 1
fi
echo "[browser] Using: $CHROME_BIN"

# shellcheck disable=SC2086
"$CHROME_BIN" \
  --remote-debugging-port="${CDP_PORT}" \
  --remote-debugging-address=0.0.0.0 \
  --remote-allow-origins='*' \
  --user-data-dir=/home/pwuser/chrome-profile \
  --no-first-run \
  --disable-sync \
  --disable-default-apps \
  --no-default-browser-check \
  --no-sandbox \
  --disable-blink-features=AutomationControlled \
  --disable-features=IsolateOrigins,site-per-process \
  --disable-infobars \
  --disable-background-networking \
  --disable-background-timer-throttling \
  --disable-backgrounding-occluded-windows \
  --disable-renderer-backgrounding \
  --disable-hang-monitor \
  --disable-ipc-flooding-protection \
  --disable-popup-blocking \
  --disable-translate \
  --disable-extensions-except=/home/pwuser/stealth-extension \
  --load-extension=/home/pwuser/stealth-extension \
  --window-size="${SCREEN_WIDTH},${SCREEN_HEIGHT}" \
  $SHM_FLAGS \
  $GPU_FLAGS \
  "${START_URL}" &
sleep 3

# ────────────────────────────────────────────────────────────────
# 6. CDP 代理 + VNC + noVNC
# ────────────────────────────────────────────────────────────────
echo "[browser] Starting CDP proxy: 0.0.0.0:${CDP_PROXY_PORT} -> 127.0.0.1:${CDP_PORT}"
socat "TCP-LISTEN:${CDP_PROXY_PORT},fork,reuseaddr,bind=0.0.0.0" "TCP:127.0.0.1:${CDP_PORT}" &
sleep 1

echo "[browser] Starting x11vnc on port 5900"
VNC_ARGS="-display ${DISPLAY} -forever -shared -rfbport 5900 -noxdamage"
if [ -n "${VNC_PASSWORD:-}" ]; then
  mkdir -p /home/pwuser/.vnc
  x11vnc -storepasswd "$VNC_PASSWORD" /home/pwuser/.vnc/passwd
  VNC_ARGS="$VNC_ARGS -rfbauth /home/pwuser/.vnc/passwd"
else
  VNC_ARGS="$VNC_ARGS -nopw"
fi
# shellcheck disable=SC2086
x11vnc $VNC_ARGS &
sleep 1

echo "[browser] Starting noVNC on port 6080"
echo "[browser]   noVNC: http://localhost:6080/vnc.html"
echo "[browser]   CDP:   http://127.0.0.1:${CDP_PROXY_PORT}"
echo "[browser]   shm:   ${SHM_MB}MB | GPU: SwiftShader (software)"

exec websockify --web /usr/share/novnc 6080 localhost:5900
