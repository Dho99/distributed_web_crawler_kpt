#!/usr/bin/env bash
# Install the CrawlMesh Worker Agent as a systemd service.
# Usage: sudo ./install_agent_linux.sh --master http://192.168.18.141:8000 --token <TOKEN> [--pool-size 4]

set -euo pipefail

MASTER=""
TOKEN=""
POOL_SIZE=0
PORT=8010

while [[ $# -gt 0 ]]; do
  case "$1" in
    --master) MASTER="$2"; shift 2 ;;
    --token) TOKEN="$2"; shift 2 ;;
    --pool-size) POOL_SIZE="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$MASTER" || -z "$TOKEN" ]]; then
  echo "usage: $0 --master <url> --token <pairing-token> [--pool-size N] [--port 8010]" >&2
  exit 1
fi

if [[ $EUID -ne 0 ]]; then
  echo "run as root (sudo)" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${REPO_ROOT}/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "venv python not found at $PYTHON" >&2
  exit 1
fi

UNIT=/etc/systemd/system/crawlmesh-agent.service
cat > "$UNIT" <<EOF
[Unit]
Description=CrawlMesh Worker Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${REPO_ROOT}
Environment=CRAWLMESH_MASTER_URL=${MASTER}
Environment=CRAWLMESH_TOKEN=${TOKEN}
ExecStart=${PYTHON} -m worker.agent --port ${PORT} --pool-size ${POOL_SIZE}
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

chmod 600 "$UNIT"
systemctl daemon-reload
systemctl enable --now crawlmesh-agent.service

echo "crawlmesh-agent.service installed and started"
echo "logs: journalctl -u crawlmesh-agent -f"
