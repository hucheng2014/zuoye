#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage:
  tools/agent-browser.sh list
  tools/agent-browser.sh connect <target>
  tools/agent-browser.sh <target> <agent-browser command> [args...]

Examples:
  tools/agent-browser.sh asr snapshot -i
  tools/agent-browser.sh alibaba screenshot /tmp/alibaba.png
  tools/agent-browser.sh work-a get url
  tools/agent-browser.sh duomotai find text "提交" click

Targets:
  asr, putonghuaasr
  oneform
  work-a, controlled
  work-b, trae, traedocker
  alibaba, alibabaxiangmu
  duomotai
EOF
}

target_spec() {
  local target="${1:-}"
  case "$target" in
    asr|putonghuaasr)
      echo "asr|zuoye-asr|http://127.0.0.1:9221|http://127.0.0.1:6080/vnc.html|Putonghua ASR Docker browser"
      ;;
    oneform)
      echo "oneform|zuoye-oneform|http://127.0.0.1:9225|http://127.0.0.1:6081/vnc.html|Oneform monitor browser"
      ;;
    work-a|controlled|controlled-browser)
      echo "work-a|zuoye-work-a|http://127.0.0.1:9233|http://127.0.0.1:6082/vnc.html|Primary controlled work browser"
      ;;
    work-b|trae|traedocker)
      echo "work-b|zuoye-work-b|http://127.0.0.1:9235|http://127.0.0.1:6083/vnc.html|Secondary work browser / Trae browser"
      ;;
    alibaba|alibabaxiangmu)
      echo "alibaba|zuoye-alibaba|http://127.0.0.1:9237|http://127.0.0.1:6084/vnc.html|Alibaba annotation browser"
      ;;
    duomotai)
      echo "duomotai|zuoye-duomotai|http://127.0.0.1:9239|http://127.0.0.1:6085/vnc.html|Duomotai browser"
      ;;
    *)
      return 1
      ;;
  esac
}

list_targets() {
  printf "%-24s %-28s %-36s %s\n" "TARGET" "CDP" "NOVNC" "NOTES"
  printf "%-24s %-28s %-36s %s\n" "------" "---" "-----" "-----"
  for target in asr oneform work-a work-b alibaba duomotai; do
    IFS='|' read -r id _session cdp vnc notes <<<"$(target_spec "$target")"
    printf "%-24s %-28s %-36s %s\n" "$id" "$cdp" "$vnc" "$notes"
  done
  cat <<'EOF'

Aliases:
  asr=putonghuaasr
  work-a=controlled=controlled-browser
  work-b=trae=traedocker
  alibaba=alibabaxiangmu
EOF
}

require_agent_browser() {
  if ! command -v agent-browser >/dev/null 2>&1; then
    echo "ERROR: agent-browser is not installed or not on PATH." >&2
    exit 127
  fi
}

resolve_ws_url() {
  local cdp="$1"
  python3 - "$cdp" <<'PY'
import json
import sys
import urllib.parse
import urllib.request

cdp = sys.argv[1].rstrip("/")
request = urllib.request.Request(
    cdp + "/json/version",
    headers={"Host": "localhost:9222"},
)
with urllib.request.urlopen(request, timeout=5) as response:
    data = json.loads(response.read().decode("utf-8"))

ws = data.get("webSocketDebuggerUrl")
if not ws:
    raise SystemExit("webSocketDebuggerUrl missing from /json/version")

cdp_url = urllib.parse.urlparse(cdp)
ws_url = urllib.parse.urlparse(ws)
scheme = "wss" if cdp_url.scheme == "https" else "ws"
host = cdp_url.hostname or "127.0.0.1"
netloc = host
if cdp_url.port:
    netloc += f":{cdp_url.port}"

print(urllib.parse.urlunparse((scheme, netloc, ws_url.path, ws_url.params, ws_url.query, ws_url.fragment)))
PY
}

connect_target() {
  local target="$1"
  local quiet="${2:-0}"
  local spec
  if ! spec="$(target_spec "$target")"; then
    echo "ERROR: unknown browser target: $target" >&2
    usage >&2
    exit 2
  fi

  IFS='|' read -r id session cdp vnc notes <<<"$spec"

  if agent-browser --session "$session" connect "$cdp" >/dev/null 2>&1; then
    if [[ "$quiet" != "1" ]]; then
      echo "Connected: $id"
      echo "CDP: $cdp"
      echo "noVNC: $vnc"
      echo "Session: $session"
    fi
    return 0
  fi

  local ws_url
  if ! ws_url="$(resolve_ws_url "$cdp" 2>/dev/null)"; then
    echo "ERROR: cannot reach $id CDP endpoint: $cdp" >&2
    echo "Open noVNC if manual recovery is needed: $vnc" >&2
    exit 1
  fi

  agent-browser --session "$session" connect "$ws_url" >/dev/null
  if [[ "$quiet" != "1" ]]; then
    echo "Connected: $id"
    echo "CDP: $cdp"
    echo "noVNC: $vnc"
    echo "Session: $session"
  fi
}

main() {
  require_agent_browser

  if [[ $# -eq 0 ]]; then
    usage
    exit 0
  fi

  case "$1" in
    -h|--help|help)
      usage
      exit 0
      ;;
    list|targets)
      list_targets
      exit 0
      ;;
    connect)
      if [[ $# -ne 2 ]]; then
        echo "ERROR: connect requires exactly one target." >&2
        usage >&2
        exit 2
      fi
      connect_target "$2" 0
      exit 0
      ;;
  esac

  local target="$1"
  shift
  if [[ $# -eq 0 ]]; then
    set -- snapshot -i
  fi

  local spec
  if ! spec="$(target_spec "$target")"; then
    echo "ERROR: unknown browser target: $target" >&2
    usage >&2
    exit 2
  fi
  IFS='|' read -r _id session _cdp _vnc _notes <<<"$spec"

  connect_target "$target" 1
  exec agent-browser --session "$session" "$@"
}

main "$@"
