#!/usr/bin/env bash
# Restore ONE Homestead instance from a snapshot made by backup.sh.
# DESTRUCTIVE: overwrites the live database and the media volume for the target instance.
# Requires an explicit confirmation unless --yes is passed.
#
# Usage:
#   bash ops/backup/restore.sh <INSTANCE_NAME> <BACKUP_DIR> [--yes]
#     <INSTANCE_NAME>  compose project to restore INTO (must be running).
#     <BACKUP_DIR>     a dated snapshot dir containing db.sql.gz and/or media.tar.gz,
#                      e.g. ~/backups/vanwashpro-preview/2026-07-02_031500
#     --yes            skip the interactive "type the instance name" confirmation.
#
# What it does:
#   db.sql.gz    → gunzip | psql  (into the running postgres container)
#   media.tar.gz → wiped + re-extracted into the <project>_media-data volume
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# ── args ────────────────────────────────────────────────────────────────────────────────
INSTANCE=""
SNAP=""
ASSUME_YES=0
for arg in "$@"; do
  case "$arg" in
    --yes|-y) ASSUME_YES=1;;
    -*)       echo "unknown flag: $arg (only --yes is supported)"; exit 1;;
    *)        if [ -z "$INSTANCE" ]; then INSTANCE="$arg"; elif [ -z "$SNAP" ]; then SNAP="$arg";
              else echo "too many arguments: $arg"; exit 1; fi;;
  esac
done
if [ -z "$INSTANCE" ] || [ -z "$SNAP" ]; then
  echo "usage: bash ops/backup/restore.sh <INSTANCE_NAME> <BACKUP_DIR> [--yes]"; exit 1
fi

SNAP="$(cd "$SNAP" 2>/dev/null && pwd || true)"
[ -n "$SNAP" ] && [ -d "$SNAP" ] || { echo "[restore] ❌ backup dir not found"; exit 1; }

DB_GZ="$SNAP/db.sql.gz"
MEDIA_TGZ="$SNAP/media.tar.gz"
[ -f "$DB_GZ" ]    || echo "[restore] note: no db.sql.gz in snapshot — DB will be left untouched"
[ -f "$MEDIA_TGZ" ] || echo "[restore] note: no media.tar.gz in snapshot — media will be left untouched"
if [ ! -f "$DB_GZ" ] && [ ! -f "$MEDIA_TGZ" ]; then
  echo "[restore] ❌ snapshot has neither db.sql.gz nor media.tar.gz"; exit 1
fi

# ── credentials from this instance's .env (same resolution as backup.sh) ─────────────────
env_get(){ # key default
  local v=""
  [ -f "$REPO_ROOT/.env" ] && v="$(grep -E "^$1=" "$REPO_ROOT/.env" | head -n1 | cut -d= -f2- | tr -d '\042\047' || true)"
  echo "${v:-$2}"
}
PG_USER="$(env_get POSTGRES_USER homestead_site)"
PG_DB="$(env_get POSTGRES_DB   homestead_site)"
MEDIA_VOLUME="${INSTANCE}_media-data"

compose(){ docker compose -p "$INSTANCE" "$@"; }

echo "[restore] instance : $INSTANCE"
echo "[restore] snapshot : $SNAP"
echo "[restore] pg       : user=$PG_USER db=$PG_DB (service: postgres)"
echo "[restore] media vol: $MEDIA_VOLUME"

# ── preflight ───────────────────────────────────────────────────────────────────────────
command -v docker >/dev/null || { echo "[restore] ❌ docker not found on PATH"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "[restore] ❌ docker compose v2 required"; exit 1; }
if ! compose ps --status running --services 2>/dev/null | grep -qx postgres; then
  echo "[restore] ❌ postgres service is not running for project '$INSTANCE'. Start it first."
  exit 1
fi

# ── loud warning + confirmation ─────────────────────────────────────────────────────────
echo
echo "  ┌───────────────────────────────────────────────────────────────────┐"
echo "  │  WARNING: this OVERWRITES live data for instance '$INSTANCE'.       "
echo "  │  - Postgres db '$PG_DB' will be dropped/recreated and reloaded.     "
echo "  │  - Media volume '$MEDIA_VOLUME' will be WIPED and re-extracted.     "
echo "  │  This cannot be undone. Take a fresh backup.sh snapshot first.      "
echo "  └───────────────────────────────────────────────────────────────────┘"
echo
if [ "$ASSUME_YES" != 1 ]; then
  printf "Type the instance name '%s' to proceed: " "$INSTANCE"
  read -r reply
  [ "$reply" = "$INSTANCE" ] || { echo "[restore] aborted (no match)."; exit 1; }
fi

# ── restore DB ──────────────────────────────────────────────────────────────────────────
if [ -f "$DB_GZ" ]; then
  echo "[restore] 1/2 reloading Postgres from db.sql.gz …"
  # DROP/CREATE gives a clean target so the dump's own CREATE/COPY statements apply
  # against an empty schema instead of colliding with existing rows.
  echo "[restore]     dropping & recreating database '$PG_DB' (via 'postgres' maintenance db)…"
  compose exec -T postgres psql -U "$PG_USER" -d postgres -v ON_ERROR_STOP=1 \
    -c "DROP DATABASE IF EXISTS \"$PG_DB\" WITH (FORCE);" \
    -c "CREATE DATABASE \"$PG_DB\" OWNER \"$PG_USER\";"
  echo "[restore]     loading dump…"
  if gunzip -c "$DB_GZ" | compose exec -T postgres psql -U "$PG_USER" -d "$PG_DB" -v ON_ERROR_STOP=1 >/dev/null; then
    echo "[restore]     ok"
  else
    echo "[restore] ❌ psql load failed — the database may be partially restored. Investigate before serving traffic."
    exit 1
  fi
else
  echo "[restore] 1/2 skipping DB (no db.sql.gz)"
fi

# ── restore media ───────────────────────────────────────────────────────────────────────
if [ -f "$MEDIA_TGZ" ]; then
  echo "[restore] 2/2 restoring media volume '$MEDIA_VOLUME' …"
  docker volume create "$MEDIA_VOLUME" >/dev/null
  # Wipe existing contents, then untar the snapshot into the volume.
  if docker run --rm \
        -v "${MEDIA_VOLUME}:/m" \
        -v "${SNAP}:/in:ro" \
        alpine sh -c 'rm -rf /m/..?* /m/.[!.]* /m/* 2>/dev/null; tar xzf /in/media.tar.gz -C /m'; then
    echo "[restore]     ok"
  else
    echo "[restore] ❌ media restore failed."
    exit 1
  fi
  echo "[restore]     note: restart the backend so it re-reads media if needed:"
  echo "                docker compose -p $INSTANCE restart backend"
else
  echo "[restore] 2/2 skipping media (no media.tar.gz)"
fi

echo "[restore] ✅ done."
