#!/usr/bin/env bash
# Write .env + backend/.env for a Homestead deploy from environment variables. Idempotent.
# Generates strong secrets if not supplied. Run from anywhere inside the repo.
#
# Required: SITE_DOMAIN API_DOMAIN ADMIN_EMAIL
# Optional: SITE_NAME (default Homestead) · SITE_LOCALES (default en) ·
#           SITE_INDUSTRY / SITE_AUDIENCE / SITE_REGION (first-boot demo seed) ·
#           INSTANCE_NAME / FRONTEND_PORT / BACKEND_PORT / POSTGRES_PORT (multi-instance,
#           see docs/multi-instance.md) · WEBCHAT_ENABLED / WEBCHAT_BRIDGE_URL /
#           WEBCHAT_BRIDGE_TOKEN (auto-detected from ops/webchat-bridge/.env if present) ·
#           GOOGLE_CLIENT_ID · DEEPSEEK_API_KEY · POSTGRES_PASSWORD · SECRET_KEY
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo "$(dirname "$0")/../..")"

: "${SITE_DOMAIN:?set SITE_DOMAIN}"; : "${API_DOMAIN:?set API_DOMAIN}"; : "${ADMIN_EMAIL:?set ADMIN_EMAIL}"
SITE_NAME="${SITE_NAME:-Homestead}"
SITE_LOCALES="${SITE_LOCALES:-en}"
SITE_INDUSTRY="${SITE_INDUSTRY:-education}"
SITE_AUDIENCE="${SITE_AUDIENCE:-students and independent creators}"
SITE_REGION="${SITE_REGION:-United States}"
INSTANCE_NAME="${INSTANCE_NAME:-homestead-site}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
POSTGRES_PORT="${POSTGRES_PORT:-55433}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}"
SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID:-}"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"

# webchat — if the host bridge is configured (ops/webchat-bridge/.env), carry its token
# and port over so backend↔bridge auth matches without hand-copying. Explicit env wins.
WEBCHAT_ENABLED="${WEBCHAT_ENABLED:-true}"
WEBCHAT_BRIDGE_URL="${WEBCHAT_BRIDGE_URL:-}"
WEBCHAT_BRIDGE_TOKEN="${WEBCHAT_BRIDGE_TOKEN:-}"
if [ -f ops/webchat-bridge/.env ]; then
  bridge_token=$(sed -n 's/^WEBCHAT_BRIDGE_TOKEN=//p' ops/webchat-bridge/.env | tail -n 1)
  bridge_port=$(sed -n 's/^WEBCHAT_BRIDGE_PORT=//p' ops/webchat-bridge/.env | tail -n 1)
  [ -z "$WEBCHAT_BRIDGE_TOKEN" ] && [ "$bridge_token" != "change-me-to-a-long-random-string" ] \
    && WEBCHAT_BRIDGE_TOKEN="$bridge_token"
  [ -z "$WEBCHAT_BRIDGE_URL" ] && [ -n "$WEBCHAT_BRIDGE_TOKEN" ] \
    && WEBCHAT_BRIDGE_URL="http://host.docker.internal:${bridge_port:-18791}"
fi

# root .env — compose ${} substitution: instance/ports + postgres creds + frontend build args
# (domain + locales + webchat toggle are baked at build)
cat > .env <<EOF
INSTANCE_NAME=$INSTANCE_NAME
FRONTEND_PORT=$FRONTEND_PORT
BACKEND_PORT=$BACKEND_PORT
POSTGRES_DB=homestead
POSTGRES_USER=homestead
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_PORT=$POSTGRES_PORT
NEXT_PUBLIC_API_BASE_URL=https://$API_DOMAIN/api
NEXT_PUBLIC_SITE_URL=https://$SITE_DOMAIN
NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
NEXT_PUBLIC_SITE_LOCALES=$SITE_LOCALES
NEXT_PUBLIC_DEFAULT_LOCALE=${SITE_LOCALES%%,*}
NEXT_PUBLIC_WEBCHAT_ENABLED=$WEBCHAT_ENABLED
EOF

# backend/.env — DATABASE_URL is overridden by compose (points at the postgres service), so it's omitted here
cat > backend/.env <<EOF
FLASK_ENV=production
SECRET_KEY=$SECRET_KEY
CORS_ORIGINS=https://$SITE_DOMAIN
SITE_NAME=$SITE_NAME
SITE_URL=https://$SITE_DOMAIN
API_PUBLIC_URL=https://$API_DOMAIN
SITE_LOCALES=$SITE_LOCALES
SITE_DEFAULT_LOCALE=${SITE_LOCALES%%,*}
SITE_INDUSTRY=$SITE_INDUSTRY
SITE_AUDIENCE=$SITE_AUDIENCE
SITE_REGION=$SITE_REGION
GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
ADMIN_EMAILS=$ADMIN_EMAIL
DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY
WEBCHAT_ENABLED=$WEBCHAT_ENABLED
WEBCHAT_BRIDGE_URL=$WEBCHAT_BRIDGE_URL
WEBCHAT_BRIDGE_TOKEN=$WEBCHAT_BRIDGE_TOKEN
EOF

echo "[make-env] wrote .env + backend/.env"
echo "[make-env]   site=$SITE_DOMAIN  api=$API_DOMAIN  admin=$ADMIN_EMAIL  name=$SITE_NAME  locales=$SITE_LOCALES"
echo "[make-env]   instance=$INSTANCE_NAME  ports=$FRONTEND_PORT/$BACKEND_PORT/$POSTGRES_PORT (frontend/backend/postgres, 127.0.0.1 only)"
echo "[make-env]   industry=$SITE_INDUSTRY  audience=$SITE_AUDIENCE  region=$SITE_REGION"
[ -z "$GOOGLE_CLIENT_ID" ] && echo "[make-env]   (no GOOGLE_CLIENT_ID → browser login off; use 'flask token issue' for admin)"
[ "$WEBCHAT_ENABLED" = true ] && [ -z "$WEBCHAT_BRIDGE_TOKEN" ] \
  && echo "[make-env]   (webchat widget on, but no bridge token → lead-capture form only; see ops/webchat-bridge/)"
exit 0
