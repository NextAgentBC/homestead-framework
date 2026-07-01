#!/usr/bin/env bash
# One-command Homestead deploy: env → edge network → build → health → admin token →
# optional preset → Cloudflare tunnel → verify → report. Wraps the AGENT-DEPLOY.md steps.
# Idempotent: every step reconciles, so re-running after a failure is safe.
#
# Required env:
#   SITE_DOMAIN API_DOMAIN ADMIN_EMAIL
#   CF_API_TOKEN CF_ACCOUNT_ID           (unless --skip-tunnel)
# Optional env:
#   everything make-env.sh accepts — INSTANCE_NAME / FRONTEND_PORT / BACKEND_PORT /
#   POSTGRES_PORT / SITE_NAME / SITE_LOCALES / SITE_INDUSTRY / SITE_AUDIENCE / SITE_REGION …
#   HOMESTEAD_PRESET   apply a built-in style preset after first boot (e.g. education, tech)
#   TUNNEL_NAME / EDGE_NET   see setup-tunnel.sh (both default from INSTANCE_NAME)
# Flags:
#   --skip-tunnel   skip the Cloudflare API tunnel step (manual cert.pem / own-nginx flows);
#                   public reachability in verify becomes a warning instead of a failure.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo "$(dirname "$0")/../..")"

SKIP_TUNNEL=0
for arg in "$@"; do case "$arg" in
  --skip-tunnel) SKIP_TUNNEL=1;;
  *) echo "unknown flag: $arg (only --skip-tunnel is supported)"; exit 1;;
esac; done

usage(){
  cat <<'EOF'
usage: export SITE_DOMAIN=site.example.com API_DOMAIN=api.example.com ADMIN_EMAIL=you@example.com
       export CF_API_TOKEN=… CF_ACCOUNT_ID=…        # omit with --skip-tunnel
       bash ops/agent/deploy.sh [--skip-tunnel]
Multi-instance (same host): also export INSTANCE_NAME + FRONTEND_PORT/BACKEND_PORT/POSTGRES_PORT
— see docs/multi-instance.md. Full walkthrough: AGENT-DEPLOY.md.
EOF
  exit 1
}

STEP="preflight"
trap '[ $? -ne 0 ] && echo "[deploy] ❌ failed during step: $STEP — fix and re-run (idempotent)." >&2' EXIT

# ── 1/8 preflight: tools + required values, fail fast before changing anything ──────────
echo "[deploy] 1/8 preflight…"
miss=0
for b in docker jq openssl curl; do command -v "$b" >/dev/null || { echo "  MISSING tool: $b"; miss=1; }; done
docker compose version >/dev/null 2>&1 || { echo "  MISSING: docker compose v2"; miss=1; }
[ "$miss" = 1 ] && exit 1
[ -n "${SITE_DOMAIN:-}" ] && [ -n "${API_DOMAIN:-}" ] && [ -n "${ADMIN_EMAIL:-}" ] || usage
if [ "$SKIP_TUNNEL" = 0 ]; then
  [ -n "${CF_API_TOKEN:-}" ] && [ -n "${CF_ACCOUNT_ID:-}" ] \
    || { echo "  tunnel step needs CF_API_TOKEN + CF_ACCOUNT_ID (or pass --skip-tunnel)."; usage; }
fi
BACKEND_PORT="${BACKEND_PORT:-8000}"; FRONTEND_PORT="${FRONTEND_PORT:-3000}"
TUNNEL_NAME="${TUNNEL_NAME:-${INSTANCE_NAME:-homestead}}"
# compose project name follows INSTANCE_NAME so N clones coexist on one host. Only add -p
# when INSTANCE_NAME is explicitly exported (unset ⇒ default directory-name project) —
# make-env.sh mirrors this by only writing INSTANCE_NAME= into .env when it's set, so
# update.sh's env-file readback stays in sync with the project this script actually used.
compose(){ docker compose ${INSTANCE_NAME:+-p "$INSTANCE_NAME"} "$@"; }

# ── 2/8 env files (secrets auto-generated, idempotent) ──────────────────────────────────
STEP="make-env"
echo "[deploy] 2/8 writing env files…"
bash ops/agent/make-env.sh

# ── 3/8 shared edge network (tunnel ↔ app containers) ───────────────────────────────────
STEP="edge network"
echo "[deploy] 3/8 ensuring '${EDGE_NET:-edge}' network…"
docker network create "${EDGE_NET:-edge}" >/dev/null 2>&1 || true

# ── 4/8 build + start (migrations auto-run on boot) ─────────────────────────────────────
STEP="compose up"
echo "[deploy] 4/8 docker compose up -d --build${INSTANCE_NAME:+  (project: $INSTANCE_NAME)}…"
compose up -d --build

STEP="backend health"
echo "[deploy]     waiting for backend health (max 120s)…"
healthy=0
for i in $(seq 1 40); do
  compose exec -T backend python -c \
    "import urllib.request as u;u.urlopen('http://localhost:8000/api/health',timeout=3)" 2>/dev/null \
    && { healthy=1; break; }
  curl -fsS -m 3 "http://127.0.0.1:$BACKEND_PORT/api/health" >/dev/null 2>&1 && { healthy=1; break; }
  sleep 3
done
[ "$healthy" = 1 ] || { echo "  backend never became healthy — check: compose logs backend"; exit 1; }
echo "[deploy]     backend healthy."

# ── 5/8 admin token (CLI mint — no browser/OAuth needed) ────────────────────────────────
STEP="token issue"
echo "[deploy] 5/8 issuing admin token for $ADMIN_EMAIL…"
ADMIN_TOKEN="$(compose exec -T backend flask --app app.main token issue --email "$ADMIN_EMAIL" | tail -n 1 | tr -d '\r')"
[ -n "$ADMIN_TOKEN" ] || { echo "  token issue produced no output (is $ADMIN_EMAIL in ADMIN_EMAILS?)"; exit 1; }

# ── 6/8 optional starting design preset ──────────────────────────────────────────────────
STEP="design preset"
if [ -n "${HOMESTEAD_PRESET:-}" ]; then
  echo "[deploy] 6/8 applying preset '$HOMESTEAD_PRESET'…"
  curl -fsS -X POST "http://127.0.0.1:$BACKEND_PORT/api/admin/design/generate" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
    -d "{\"preset\":\"$HOMESTEAD_PRESET\"}" >/dev/null
else
  echo "[deploy] 6/8 no HOMESTEAD_PRESET — keeping the auto-seeded \${SITE_INDUSTRY} demo."
fi

# ── 7/8 public ingress: Cloudflare tunnel ────────────────────────────────────────────────
STEP="tunnel"
if [ "$SKIP_TUNNEL" = 0 ]; then
  echo "[deploy] 7/8 setting up Cloudflare tunnel '$TUNNEL_NAME'…"
  TUNNEL_NAME="$TUNNEL_NAME" bash ops/agent/setup-tunnel.sh
  echo "[deploy]     letting DNS settle (30s)…"; sleep 30
else
  echo "[deploy] 7/8 --skip-tunnel: set up ingress yourself (cert.pem cloudflared flow or"
  echo "         ops/nginx/) pointing at the '${INSTANCE_NAME:-homestead-site}-frontend/-backend' aliases on '${EDGE_NET:-edge}'."
fi

# ── 8/8 verify (the success gate) ────────────────────────────────────────────────────────
STEP="verify"
echo "[deploy] 8/8 verifying…"
if [ "$SKIP_TUNNEL" = 1 ]; then
  # local reachability is still a hard gate even without a tunnel; only the public/tunnel
  # checks (which are expected to fail before manual ingress exists) are advisory.
  SKIP_PUBLIC=1 FRONTEND_PORT="$FRONTEND_PORT" BACKEND_PORT="$BACKEND_PORT" bash ops/agent/verify.sh
  if ! FRONTEND_PORT="$FRONTEND_PORT" BACKEND_PORT="$BACKEND_PORT" bash ops/agent/verify.sh; then
    echo "[deploy] ⚠ public checks failed — expected before your manual tunnel is up."
    echo "         re-run 'bash ops/agent/verify.sh' once ingress is in place."
  fi
else
  if ! FRONTEND_PORT="$FRONTEND_PORT" BACKEND_PORT="$BACKEND_PORT" bash ops/agent/verify.sh; then
    echo "[deploy]     retrying once after a cloudflared restart (new container IPs)…"
    docker restart "${TUNNEL_NAME}-cloudflared" >/dev/null 2>&1 || true
    sleep 30
    FRONTEND_PORT="$FRONTEND_PORT" BACKEND_PORT="$BACKEND_PORT" bash ops/agent/verify.sh
  fi
fi

trap - EXIT
cat <<EOF

[deploy] ✅ done.
  site         https://$SITE_DOMAIN
  api          https://$API_DOMAIN/api
  admin token  $ADMIN_TOKEN
Next steps:
  - keep the token safe: it is the Bearer auth for /api/admin/* and the OpenClaw skills
    (point homestead-site-shared's HOMESTEAD_SITE_API at https://$API_DOMAIN/api).
  - rebrand to the client's industry:  POST /api/admin/site/rebrand {"industry":"…","brandName":"…"}
  - after any 'compose up' that recreates containers:  docker restart ${TUNNEL_NAME}-cloudflared
  - update later with:  bash ops/agent/update.sh
EOF
