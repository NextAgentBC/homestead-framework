#!/usr/bin/env bash
# Fan a single op out across every Homestead instance listed in a fleet CSV.
# From the 5th customer on, running update/verify/backup by hand on each clone doesn't
# scale — this loops the CSV, runs the matching ops/agent (or ops/backup) script per
# instance with that row's INSTANCE_NAME + domains + ports, and prints a pass/fail table.
#
# Usage:
#   bash ops/fleet/all.sh <update|verify|backup|token> <instances.csv>
#
# Actions (per row):
#   update   cd dir; INSTANCE_NAME/TUNNEL_NAME/…/ports → ops/agent/update.sh   (git pull + rebuild + retunnel + verify)
#   verify   cd dir; SITE_DOMAIN/API_DOMAIN/ports      → ops/agent/verify.sh   (local + public reachability)
#   backup   cd dir; INSTANCE_NAME                      → ops/backup/backup.sh  (pg dump + media tar)
#   token    cd dir; mint a fresh admin token for the row's instance (flask token issue in-container)
#
# CSV format: see ops/fleet/instances.example.csv. Header + '#'-comment lines are skipped.
# Columns (in order): instance,dir,site_domain,api_domain,tunnel_name,frontend_port,backend_port
#
# Failure policy: one instance failing does NOT abort the batch — every failure is caught,
# the loop continues, and the script exits non-zero at the end if ANY row failed. That way
# an unattended cron/CI run touches all instances and still signals overall health.
set -euo pipefail

ACTION="${1:-}"
CSV="${2:-}"

usage(){
  cat <<'EOF'
usage: bash ops/fleet/all.sh <update|verify|backup|token> <instances.csv>
  update  git pull + rebuild + restart tunnel + verify, per instance (ops/agent/update.sh)
  verify  local + public reachability, per instance            (ops/agent/verify.sh)
  backup  Postgres dump + media tarball, per instance          (ops/backup/backup.sh)
  token   mint a fresh admin token, per instance               (flask token issue)
CSV: copy ops/fleet/instances.example.csv → instances.csv and keep it current.
EOF
  exit 2
}

case "$ACTION" in update|verify|backup|token) ;; *) usage;; esac
[ -n "$CSV" ] && [ -f "$CSV" ] || { echo "[fleet] csv not found: '$CSV'"; usage; }

# repo root of THIS clone — where ops/agent + ops/backup live (scripts are shared code,
# per-instance state lives in each row's own 'dir').
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# backup.sh lives outside ops/agent and may not exist on older clones — probe once, up front.
BACKUP_SH="$REPO_ROOT/ops/backup/backup.sh"
if [ "$ACTION" = backup ] && [ ! -f "$BACKUP_SH" ]; then
  echo "[fleet] ❌ action 'backup' needs $BACKUP_SH but it's missing."
  echo "        (Pull the ops/backup toolchain into this clone, or run a different action.)"
  exit 1
fi

echo "[fleet] action : $ACTION"
echo "[fleet] csv    : $CSV"
echo "[fleet] scripts: $REPO_ROOT/ops"
echo

RESULTS=()   # "instance|status" — collected, printed as a table at the end
ANY_FAIL=0

# Run one action for one row. Never let a failure escape (set -e is disarmed inside the
# `if ! run_one …` guard below), so the loop always reaches the next row.
run_one(){
  local instance="$1" dir="$2" site="$3" api="$4" tunnel="$5" fport="$6" bport="$7"

  if [ ! -d "$dir" ]; then
    echo "  [$instance] ❌ dir not found: $dir"
    return 1
  fi

  case "$ACTION" in
    update)
      ( cd "$dir" \
        && INSTANCE_NAME="$instance" TUNNEL_NAME="$tunnel" \
           SITE_DOMAIN="$site" API_DOMAIN="$api" \
           FRONTEND_PORT="$fport" BACKEND_PORT="$bport" \
           bash "$REPO_ROOT/ops/agent/update.sh" )
      ;;
    verify)
      ( cd "$dir" \
        && SITE_DOMAIN="$site" API_DOMAIN="$api" \
           FRONTEND_PORT="$fport" BACKEND_PORT="$bport" \
           bash "$REPO_ROOT/ops/agent/verify.sh" )
      ;;
    backup)
      ( cd "$dir" \
        && INSTANCE_NAME="$instance" \
           bash "$BACKUP_SH" "$instance" )
      ;;
    token)
      # Mint against the row's own compose project. -p keeps N clones from colliding.
      ( cd "$dir" \
        && docker compose -p "$instance" exec -T backend \
             flask --app app.main token issue | tail -n 1 | tr -d '\r' )
      ;;
  esac
}

# ── loop the CSV ─────────────────────────────────────────────────────────────────────────
# Skip blank lines, '#'-comments, and the header row (first field literally 'instance').
while IFS=',' read -r instance dir site api tunnel fport bport _rest; do
  # trim surrounding whitespace on the key field; skip blanks/comments/header
  instance="${instance#"${instance%%[![:space:]]*}"}"
  instance="${instance%"${instance##*[![:space:]]}"}"
  case "$instance" in ''|\#*|instance) continue;; esac

  echo "── [$instance]  ($ACTION) ──────────────────────────────────────────────"
  if run_one "$instance" "$dir" "$site" "$api" "$tunnel" "$fport" "$bport"; then
    echo "  [$instance] ✅ ok"
    RESULTS+=("$instance|ok")
  else
    echo "  [$instance] ❌ failed"
    RESULTS+=("$instance|FAIL")
    ANY_FAIL=1
  fi
  echo
done < "$CSV"

# ── summary table ────────────────────────────────────────────────────────────────────────
echo "════════ fleet $ACTION summary ════════"
if [ "${#RESULTS[@]}" -eq 0 ]; then
  echo "  (no instance rows found in $CSV)"
  exit 1
fi
printf '  %-28s %s\n' "INSTANCE" "STATUS"
for r in "${RESULTS[@]}"; do
  printf '  %-28s %s\n' "${r%%|*}" "${r##*|}"
done
echo "═══════════════════════════════════════"

if [ "$ANY_FAIL" -ne 0 ]; then
  echo "[fleet] ❌ one or more instances failed '$ACTION' — see logs above."
  exit 1
fi
echo "[fleet] ✅ all instances succeeded '$ACTION'."
