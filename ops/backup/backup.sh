#!/usr/bin/env bash
# Back up ONE Homestead instance: Postgres dump (gzip) + media named-volume tarball.
# Paying-customer data safety net — losing it is a business incident, so every step is
# verbose and any failure aborts (no silent half-backups). Idempotent per run: each run
# writes a fresh dated directory, then prunes old ones.
#
# Usage:
#   bash ops/backup/backup.sh [INSTANCE_NAME]
#   INSTANCE_NAME (arg or env) selects the compose project; defaults to the instance's
#   own .env INSTANCE_NAME, then the clone directory name.
#
# Resolution order for the instance name:
#   1) $1 (positional arg)   2) $INSTANCE_NAME env   3) INSTANCE_NAME= in ./.env
#   4) basename of the repo root (matches Docker Compose's default project name)
#
# Env knobs:
#   BACKUP_DIR   destination root (default: ~/backups)
#   KEEP         how many dated snapshots to retain per instance (default: 7)
#
# What it produces:
#   $BACKUP_DIR/<instance>/<YYYY-MM-DD_HHMMSS>/db.sql.gz     (pg_dump | gzip)
#   $BACKUP_DIR/<instance>/<YYYY-MM-DD_HHMMSS>/media.tar.gz  (tar of the media volume)
#   $BACKUP_DIR/<instance>/<YYYY-MM-DD_HHMMSS>/MANIFEST.txt  (what/when/versions)
set -euo pipefail

# ── repo root = the clone directory (also Compose's default project name) ────────────────
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# ── resolve the instance / compose project name ─────────────────────────────────────────
INSTANCE="${1:-${INSTANCE_NAME:-}}"
if [ -z "$INSTANCE" ] && [ -f "$REPO_ROOT/.env" ]; then
  # pull INSTANCE_NAME= out of .env without sourcing (avoids executing arbitrary values)
  INSTANCE="$(grep -E '^INSTANCE_NAME=' "$REPO_ROOT/.env" | head -n1 | cut -d= -f2- | tr -d '\042\047' || true)"
fi
INSTANCE="${INSTANCE:-$(basename "$REPO_ROOT")}"

# ── read Postgres credentials from this instance's .env (fall back to compose defaults) ──
env_get(){ # key default
  local v=""
  [ -f "$REPO_ROOT/.env" ] && v="$(grep -E "^$1=" "$REPO_ROOT/.env" | head -n1 | cut -d= -f2- | tr -d '\042\047' || true)"
  echo "${v:-$2}"
}
PG_USER="$(env_get POSTGRES_USER homestead_site)"   # compose default is homestead_site
PG_DB="$(env_get POSTGRES_DB   homestead_site)"

# ── knobs ───────────────────────────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
KEEP="${KEEP:-7}"
STAMP="$(date +%F_%H%M%S)"
DEST="$BACKUP_DIR/$INSTANCE/$STAMP"
# Media volume = "<compose project>_media-data" (see docker-compose.yml `volumes:`).
# The Compose project name == INSTANCE for the deploys made by ops/agent/deploy.sh.
MEDIA_VOLUME="${INSTANCE}_media-data"

# compose helper mirrors ops/agent/deploy.sh: only pass -p when we have an instance name.
compose(){ docker compose -p "$INSTANCE" "$@"; }

echo "[backup] instance : $INSTANCE"
echo "[backup] pg        : user=$PG_USER db=$PG_DB (service: postgres)"
echo "[backup] media vol : $MEDIA_VOLUME"
echo "[backup] dest      : $DEST"
echo "[backup] keep      : $KEEP snapshots"

# ── preflight: tools present, project actually running, volume exists ────────────────────
command -v docker >/dev/null || { echo "[backup] ❌ docker not found on PATH"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "[backup] ❌ docker compose v2 required"; exit 1; }
if ! compose ps --status running --services 2>/dev/null | grep -qx postgres; then
  echo "[backup] ❌ postgres service is not running for project '$INSTANCE'."
  echo "         Start it first (ops/agent/deploy.sh) or pass the correct INSTANCE_NAME."
  exit 1
fi
if ! docker volume inspect "$MEDIA_VOLUME" >/dev/null 2>&1; then
  echo "[backup] ❌ media volume '$MEDIA_VOLUME' not found. Existing volumes:"
  docker volume ls --format '  {{.Name}}' | grep -i media-data || true
  exit 1
fi

mkdir -p "$DEST"

# ── 1/2 Postgres dump → gzip ────────────────────────────────────────────────────────────
# -T: no TTY (piping). pg_dump runs INSIDE the container so no host psql client is needed.
echo "[backup] 1/2 pg_dump → db.sql.gz …"
if compose exec -T postgres pg_dump -U "$PG_USER" "$PG_DB" | gzip > "$DEST/db.sql.gz"; then
  echo "[backup]     ok  ($(du -h "$DEST/db.sql.gz" | cut -f1))"
else
  echo "[backup] ❌ pg_dump failed — removing partial snapshot dir"; rm -rf "$DEST"; exit 1
fi
# gzip -0 empty output would still succeed; guard against a suspiciously tiny dump.
if [ ! -s "$DEST/db.sql.gz" ]; then
  echo "[backup] ❌ db.sql.gz is empty — aborting"; rm -rf "$DEST"; exit 1
fi

# ── 2/2 media volume → tarball ──────────────────────────────────────────────────────────
# Mount the named volume read-only into a throwaway alpine and tar its contents.
echo "[backup] 2/2 tar media volume → media.tar.gz …"
if docker run --rm \
      -v "${MEDIA_VOLUME}:/m:ro" \
      -v "${DEST}:/out" \
      alpine tar czf /out/media.tar.gz -C /m . ; then
  echo "[backup]     ok  ($(du -h "$DEST/media.tar.gz" | cut -f1))"
else
  echo "[backup] ❌ media tar failed — removing partial snapshot dir"; rm -rf "$DEST"; exit 1
fi

# ── manifest (so restore.sh / a human knows exactly what this is) ────────────────────────
{
  echo "instance:      $INSTANCE"
  echo "created:       $(date -Is)"
  echo "postgres_user: $PG_USER"
  echo "postgres_db:   $PG_DB"
  echo "media_volume:  $MEDIA_VOLUME"
  echo "db_dump:       db.sql.gz"
  echo "media_tar:     media.tar.gz"
} > "$DEST/MANIFEST.txt"

# ── retention: keep the newest $KEEP dated dirs, delete older ones ───────────────────────
echo "[backup] pruning old snapshots (keep $KEEP)…"
INST_ROOT="$BACKUP_DIR/$INSTANCE"
# List dated dirs newest-first, skip the first $KEEP, remove the rest.
mapfile -t OLD < <(ls -1dt "$INST_ROOT"/*/ 2>/dev/null | tail -n +"$((KEEP + 1))")
if [ "${#OLD[@]}" -gt 0 ]; then
  for d in "${OLD[@]}"; do echo "  rm $d"; rm -rf "$d"; done
else
  echo "  nothing to prune"
fi

echo "[backup] ✅ done: $DEST"
