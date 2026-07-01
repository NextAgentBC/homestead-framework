#!/usr/bin/env bash
# Update a running Homestead instance: git pull → rebuild → restart cloudflared → verify.
# Encodes the deploy gotcha: recreated containers get new IPs, so the tunnel connector
# MUST be restarted or the public site returns 502/530 while local ports look fine.
#
# Optional env (all auto-derived from .env / backend/.env written by make-env.sh):
#   INSTANCE_NAME   compose project name (multi-instance hosts, see docs/multi-instance.md)
#   TUNNEL_NAME     cloudflared container prefix, default: $INSTANCE_NAME or 'homestead'
#   SITE_DOMAIN / API_DOMAIN / FRONTEND_PORT / BACKEND_PORT   for verify.sh
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo "$(dirname "$0")/../..")"

# fill unset values from the env files so a bare `bash ops/agent/update.sh` just works
envval(){ sed -n "s/^$2=//p" "$1" 2>/dev/null | tail -n 1; }
INSTANCE_NAME="${INSTANCE_NAME:-$(envval .env INSTANCE_NAME)}"
FRONTEND_PORT="${FRONTEND_PORT:-$(envval .env FRONTEND_PORT)}"
BACKEND_PORT="${BACKEND_PORT:-$(envval .env BACKEND_PORT)}"
SITE_DOMAIN="${SITE_DOMAIN:-$(envval backend/.env SITE_URL | sed 's|^https\?://||')}"
API_DOMAIN="${API_DOMAIN:-$(envval backend/.env API_PUBLIC_URL | sed 's|^https\?://||')}"
TUNNEL_NAME="${TUNNEL_NAME:-${INSTANCE_NAME:-homestead}}"

echo "[update] pulling latest…"
git pull --ff-only

echo "[update] rebuilding + restarting containers${INSTANCE_NAME:+  (project: $INSTANCE_NAME)}…"
docker compose ${INSTANCE_NAME:+-p "$INSTANCE_NAME"} up -d --build

echo "[update] restarting tunnel connector (re-resolves new container IPs)…"
if docker restart "${TUNNEL_NAME}-cloudflared" >/dev/null 2>&1; then
  echo "[update]   restarted ${TUNNEL_NAME}-cloudflared."
else
  echo "[update]   no '${TUNNEL_NAME}-cloudflared' container — skipping (restart your own ingress if needed)."
fi

echo "[update] verifying…"
sleep 10   # give the connector a moment to reconnect
SITE_DOMAIN="$SITE_DOMAIN" API_DOMAIN="$API_DOMAIN" \
  FRONTEND_PORT="${FRONTEND_PORT:-3000}" BACKEND_PORT="${BACKEND_PORT:-8000}" \
  bash ops/agent/verify.sh
echo "[update] ✅ done."
