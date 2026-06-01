#!/usr/bin/env bash
# Write .env + backend/.env for a Homestead deploy from environment variables. Idempotent.
# Generates strong secrets if not supplied. Run from anywhere inside the repo.
#
# Required: SITE_DOMAIN API_DOMAIN ADMIN_EMAIL
# Optional: SITE_NAME (default Homestead) · SITE_LOCALES (default en) ·
#           GOOGLE_CLIENT_ID · DEEPSEEK_API_KEY · POSTGRES_PASSWORD · SECRET_KEY
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo "$(dirname "$0")/../..")"

: "${SITE_DOMAIN:?set SITE_DOMAIN}"; : "${API_DOMAIN:?set API_DOMAIN}"; : "${ADMIN_EMAIL:?set ADMIN_EMAIL}"
SITE_NAME="${SITE_NAME:-Homestead}"
SITE_LOCALES="${SITE_LOCALES:-en}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}"
SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
GOOGLE_CLIENT_ID="${GOOGLE_CLIENT_ID:-}"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"

# root .env — compose ${} substitution: postgres creds + frontend build args (domain is baked at build)
cat > .env <<EOF
POSTGRES_DB=homestead
POSTGRES_USER=homestead
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_PORT=55433
NEXT_PUBLIC_API_BASE_URL=https://$API_DOMAIN/api
NEXT_PUBLIC_SITE_URL=https://$SITE_DOMAIN
NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
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
GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
ADMIN_EMAILS=$ADMIN_EMAIL
DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY
EOF

echo "[make-env] wrote .env + backend/.env"
echo "[make-env]   site=$SITE_DOMAIN  api=$API_DOMAIN  admin=$ADMIN_EMAIL  name=$SITE_NAME  locales=$SITE_LOCALES"
[ -z "$GOOGLE_CLIENT_ID" ] && echo "[make-env]   (no GOOGLE_CLIENT_ID → browser login off; use 'flask token issue' for admin)"
