#!/usr/bin/env bash
# Health probe for ONE Homestead instance — the "is this customer's site OK right now?"
# glance. Runs standalone (bare `bash ops/fleet/status.sh` against this clone) and is the
# per-row worker behind `ops/fleet/all.sh status` (fleet-wide table / JSON).
#
# It only touches things a maintainer legitimately can from the host: public reachability
# through the tunnel, container state, a trivial DB round-trip, and the newest local backup.
# None of the core probes need an admin token (kept deliberately read-only + cheap).
#
# Usage:
#   bash ops/fleet/status.sh [--json]
#
# Configured entirely by env (same names all.sh passes each CSV row):
#   INSTANCE_NAME   compose project name == clone dir name (see docs/multi-instance.md)
#   DIR             clone directory (for reading its .env creds); default: this repo root
#   SITE_DOMAIN     public site hostname   (skips public_site probe if empty)
#   API_DOMAIN      public API hostname    (skips public_api  probe if empty)
#   FRONTEND_PORT   host-published 127.0.0.1 port (default 3000)  — reserved / informational
#   BACKEND_PORT    host-published 127.0.0.1 port (default 8000)  — reserved / informational
#   WARN_BACKUP_DAYS  a backup older than this many days is WARN (default 2)
#
# Overall rollup:
#   DOWN  public site OR api unreachable, or any container not running/healthy
#   WARN  site+api up & containers ok, but backup is stale/missing (or DB/tunnel degraded)
#   OK    everything green
#
# Output:
#   default   one compact human line: instance + per-probe icons/values + overall
#   --json    one line: {instance,overall,publicSite,publicApi,containers,pages,
#                        lastBackupDays,tunnel}
#
# Robustness: `set -euo pipefail`, but EVERY probe is wrapped so a single failure degrades
# THAT probe (DOWN / n/a) instead of killing the script — a health checker must never crash
# just because one thing it's checking is broken.
set -euo pipefail

JSON=0
case "${1:-}" in
  --json) JSON=1 ;;
  '' ) ;;
  *) echo "usage: bash ops/fleet/status.sh [--json]" >&2; exit 2 ;;
esac

# ── config from env (mirror all.sh row vars; sensible standalone defaults) ────────────────
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIR="${DIR:-$REPO_ROOT}"
INSTANCE_NAME="${INSTANCE_NAME:-$(basename "$DIR")}"
SITE_DOMAIN="${SITE_DOMAIN:-}"
API_DOMAIN="${API_DOMAIN:-}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
WARN_BACKUP_DAYS="${WARN_BACKUP_DAYS:-2}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"

# compose helper mirrors deploy.sh/backup.sh: always scope to this instance's project.
compose(){ docker compose -p "$INSTANCE_NAME" "$@"; }

# read a key out of DIR/.env WITHOUT sourcing it (same approach as backup.sh env_get).
env_get(){ # key default
  local v=""
  [ -f "$DIR/.env" ] && v="$(grep -E "^$1=" "$DIR/.env" 2>/dev/null | head -n1 | cut -d= -f2- | tr -d '\042\047' || true)"
  echo "${v:-$2}"
}
PG_USER="$(env_get POSTGRES_USER homestead)"   # this env's default is homestead/homestead
PG_DB="$(env_get POSTGRES_DB   homestead)"

# ── probe 1+2: public reachability (single curl, never aborts the script) ─────────────────
# Returns "up"/"down"/"skip"; captures the observed HTTP code into the named-by-convention
# vars for the human line. `|| true` + a default keep pipefail from tripping on curl exit.
http_code(){ # url  -> prints the numeric code (000 on total failure)
  local c
  c="$(curl -sS -o /dev/null -m 20 -w '%{http_code}' "$1" 2>/dev/null || true)"
  echo "${c:-000}"
}
code_in(){ printf ' %s ' "$2" | grep -q " $1 "; }  # code  "list"

PUBLIC_SITE="skip"; SITE_CODE="-"
if [ -n "$SITE_DOMAIN" ]; then
  SITE_CODE="$(http_code "https://$SITE_DOMAIN/")"
  if code_in "$SITE_CODE" "200 301 307 308"; then PUBLIC_SITE="up"; else PUBLIC_SITE="down"; fi
fi

PUBLIC_API="skip"; API_CODE="-"
if [ -n "$API_DOMAIN" ]; then
  API_CODE="$(http_code "https://$API_DOMAIN/api/health")"
  if code_in "$API_CODE" "200"; then PUBLIC_API="up"; else PUBLIC_API="down"; fi
fi

# ── probe 3: containers — running/healthy vs total for this compose project ───────────────
# `docker compose ps` (v2) gives one line per service. Health = the service is running and,
# if it declares a healthcheck, is 'healthy' (not 'starting'/'unhealthy').
CONTAINERS="n/a"; CONT_OK=""; CONT_TOTAL=""
if command -v docker >/dev/null 2>&1; then
  # --format json emits one JSON object per line (v2). Fall back to plain if unsupported.
  ps_json="$(compose ps -a --format json 2>/dev/null || true)"
  if [ -n "$ps_json" ]; then
    # Count total services and how many are Up/healthy. Grep the per-line State/Health
    # fields rather than depending on jq being installed.
    CONT_TOTAL="$(printf '%s\n' "$ps_json" | grep -c '"Service"' || true)"
    # A service is counted OK when its State is running AND its Health is not unhealthy/starting.
    # docker compose json exposes "State":"running" and "Health":"healthy"|"starting"|"unhealthy"|"".
    CONT_OK="$(printf '%s\n' "$ps_json" \
      | grep '"State":"running"' \
      | grep -vE '"Health":"(starting|unhealthy)"' \
      | wc -l | tr -d ' ' || true)"
  else
    # Older/plain fallback: `compose ps` table; count service lines and Up ones.
    ps_txt="$(compose ps 2>/dev/null || true)"
    if [ -n "$ps_txt" ]; then
      CONT_TOTAL="$(compose ps --services 2>/dev/null | grep -cvE '^\s*$' || true)"
      CONT_OK="$(printf '%s\n' "$ps_txt" | grep -icE '\bUp\b|running|healthy' || true)"
    fi
  fi
  CONT_TOTAL="${CONT_TOTAL:-0}"; CONT_OK="${CONT_OK:-0}"
  if [ "$CONT_TOTAL" -gt 0 ]; then CONTAINERS="$CONT_OK/$CONT_TOTAL"; else CONTAINERS="0/0"; fi
fi

# containers_ok: true only when we have a real total and every one is up/healthy.
containers_ok(){ [ "$CONTAINERS" != "n/a" ] && [ "${CONT_TOTAL:-0}" -gt 0 ] && [ "${CONT_OK:-0}" -eq "${CONT_TOTAL:-0}" ]; }

# ── probe 4: DB round-trip + page count (best-effort; degraded ≠ fatal) ───────────────────
# A trivial `select count(*) from page` proves postgres is reachable AND the schema exists.
# Failure here (db down, table missing, container absent) → pages="?" and marks db degraded,
# but does NOT by itself take the whole instance DOWN (public probes decide that).
PAGES="?"; DB_OK=0
if command -v docker >/dev/null 2>&1; then
  pg_out="$(compose exec -T postgres psql -U "$PG_USER" "$PG_DB" -tAc 'select count(*) from page' 2>/dev/null || true)"
  pg_out="$(printf '%s' "$pg_out" | tr -d '[:space:]')"
  if printf '%s' "$pg_out" | grep -qE '^[0-9]+$'; then PAGES="$pg_out"; DB_OK=1; fi
fi

# ── probe 5: newest local backup, and how many days old ──────────────────────────────────
# Backups land in $BACKUP_DIR/<instance>/<YYYY-MM-DD_HHMMSS>/ (see ops/backup/backup.sh).
# We use the dir's mtime for "days old" — robust to name format and clock skew in the stamp.
LAST_BACKUP_DAYS="-1"   # -1 == none found (rendered as WARN "none")
INST_BK="$BACKUP_DIR/$INSTANCE_NAME"
if [ -d "$INST_BK" ]; then
  newest="$(ls -1dt "$INST_BK"/*/ 2>/dev/null | head -n1 || true)"
  if [ -n "$newest" ] && [ -d "$newest" ]; then
    now="$(date +%s)"
    mt="$(stat -c %Y "$newest" 2>/dev/null || echo "")"
    if [ -n "$mt" ]; then
      LAST_BACKUP_DAYS="$(( (now - mt) / 86400 ))"
    fi
  fi
fi
backup_stale(){ [ "$LAST_BACKUP_DAYS" = "-1" ] || [ "${LAST_BACKUP_DAYS}" -gt "$WARN_BACKUP_DAYS" ]; }

# ── probe 6: tunnel connector container (informational; n/a is not fatal) ─────────────────
# Container is named "<TUNNEL_NAME>-cloudflared" (ops/agent/setup-tunnel.sh, update.sh).
# TUNNEL_NAME defaults to the instance name per docs/multi-instance.md.
TUNNEL_NAME="${TUNNEL_NAME:-$INSTANCE_NAME}"
TUNNEL="n/a"
if command -v docker >/dev/null 2>&1; then
  cf_name="${TUNNEL_NAME}-cloudflared"
  up="$(docker ps --filter "name=^/${cf_name}$" --filter 'status=running' --format '{{.Names}}' 2>/dev/null || true)"
  if [ -n "$up" ]; then
    TUNNEL="up"
  else
    # exists but not running vs. doesn't exist at all → down vs n/a
    exists="$(docker ps -a --filter "name=^/${cf_name}$" --format '{{.Names}}' 2>/dev/null || true)"
    if [ -n "$exists" ]; then TUNNEL="down"; else TUNNEL="n/a"; fi
  fi
fi

# ── roll up overall ──────────────────────────────────────────────────────────────────────
# DOWN: a probed public endpoint is unreachable, OR containers exist but aren't all up.
# WARN: everything reachable but backup stale/missing, or DB unreachable, or tunnel down.
# OK  : all green.
OVERALL="OK"
if [ "$PUBLIC_SITE" = "down" ] || [ "$PUBLIC_API" = "down" ]; then
  OVERALL="DOWN"
elif [ "$CONTAINERS" != "n/a" ] && ! containers_ok; then
  OVERALL="DOWN"
else
  if backup_stale || [ "$DB_OK" -ne 1 ] || [ "$TUNNEL" = "down" ]; then
    OVERALL="WARN"
  fi
fi

# ── render ───────────────────────────────────────────────────────────────────────────────
# icon helpers for the compact human line
ico(){ case "$1" in up|ok|OK) echo "✅";; down|DOWN) echo "❌";; WARN|warn) echo "⚠️";; skip|n/a|na) echo "–";; *) echo "?";; esac; }

# backup as a short human token: "none" / "<n>d"
if [ "$LAST_BACKUP_DAYS" = "-1" ]; then bk_human="none"; else bk_human="${LAST_BACKUP_DAYS}d"; fi

if [ "$JSON" -eq 1 ]; then
  # one-line JSON for dashboard consumption. lastBackupDays: -1 means "no backup found".
  printf '{"instance":"%s","overall":"%s","publicSite":"%s","publicApi":"%s","containers":"%s","pages":%s,"lastBackupDays":%s,"tunnel":"%s"}\n' \
    "$INSTANCE_NAME" "$OVERALL" "$PUBLIC_SITE" "$PUBLIC_API" "$CONTAINERS" \
    "$([ "$PAGES" = '?' ] && echo null || echo "$PAGES")" \
    "$LAST_BACKUP_DAYS" "$TUNNEL"
else
  printf '[%s] %s  site %s(%s)  api %s(%s)  cont %s %s  pages %s  backup %s  tunnel %s %s  →  %s %s\n' \
    "$INSTANCE_NAME" "$(ico "$OVERALL")" \
    "$(ico "$PUBLIC_SITE")" "$SITE_CODE" \
    "$(ico "$PUBLIC_API")" "$API_CODE" \
    "$CONTAINERS" "$(containers_ok && echo "$(ico ok)" || { [ "$CONTAINERS" = n/a ] && echo "$(ico n/a)" || echo "$(ico down)"; })" \
    "$PAGES" \
    "$bk_human" \
    "$TUNNEL" "$(ico "$TUNNEL")" \
    "$OVERALL" "$(ico "$OVERALL")"
fi

# Exit code mirrors overall so a bare call is scriptable: DOWN=1, WARN=0 (degraded but live).
[ "$OVERALL" = "DOWN" ] && exit 1
exit 0
