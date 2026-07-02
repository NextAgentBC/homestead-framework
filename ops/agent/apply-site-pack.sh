#!/usr/bin/env bash
# Apply an exported site pack to THIS deploy: copy the pack into the backend
# container and run `flask site import`. A site pack (built with
# `flask site export`) is a portable, brand-agnostic template — the active design,
# pages, UI strings and referenced media — so a hand-tuned industry sample can be
# re-applied to a fresh instance in minutes. See docs/site-packs.md.
#
# What travels vs. what does NOT:
#   • media URLs are portable — the pack stores a __MEDIA__/ sentinel; import
#     rewrites it to THIS site's API_PUBLIC_URL, so links aren't bound to the
#     source domain, and the media files ride inside the pack.
#   • NAP (phone/email/address/geo/hours/service areas/legal name) is NEVER in a
#     pack. After applying, set this client's contact info via
#     PATCH /api/admin/site/settings (or a rebrand) — see the import's own notice.
#
# Usage:
#   bash ops/agent/apply-site-pack.sh <pack.tar.gz> [--rebrand-name "Client Co"] \
#                                     [--api-base https://newapi.example.com] [--force]
#
# Optional env:
#   INSTANCE_NAME   compose project name (multi-instance hosts; see docs/multi-instance.md).
#                   Kept in sync with deploy.sh/update.sh: -p is only passed when set.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || echo "$(dirname "$0")/../..")"

# fill INSTANCE_NAME from .env when not exported, matching deploy.sh/update.sh so
# this targets the same compose project they used.
envval(){ sed -n "s/^$2=//p" "$1" 2>/dev/null | tail -n 1 || true; }
INSTANCE_NAME="${INSTANCE_NAME:-$(envval .env INSTANCE_NAME)}"
compose(){ docker compose ${INSTANCE_NAME:+-p "$INSTANCE_NAME"} "$@"; }

usage(){
  cat <<'EOF'
usage: bash ops/agent/apply-site-pack.sh <pack.tar.gz> \
         [--rebrand-name "Client Co"] [--api-base https://newapi.example.com] [--force]

  <pack.tar.gz>       a site pack exported with `flask site export`
  --rebrand-name X    override the pack's site_name (rebrand it for this client)
  --api-base URL      base for restored media links (default: this site's API_PUBLIC_URL)
  --force             overwrite existing pages on slug conflict (default: skip + warn)

Multi-instance: export INSTANCE_NAME to target a named compose project.
Full workflow + design notes: docs/site-packs.md.
EOF
  exit 1
}

PACK=""
PASS_ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage;;
    --rebrand-name) [ $# -ge 2 ] || { echo "--rebrand-name needs a value"; usage; }
                    PASS_ARGS+=(--rebrand-name "$2"); shift 2;;
    --api-base)     [ $# -ge 2 ] || { echo "--api-base needs a value"; usage; }
                    PASS_ARGS+=(--api-base "$2"); shift 2;;
    --force)        PASS_ARGS+=(--force); shift;;
    -*)             echo "unknown flag: $1"; usage;;
    *)              [ -z "$PACK" ] || { echo "unexpected extra argument: $1"; usage; }
                    PACK="$1"; shift;;
  esac
done

[ -n "$PACK" ] || { echo "error: no pack path given."; usage; }
[ -f "$PACK" ] || { echo "error: pack not found: $PACK"; exit 1; }

# resolve the backend container id for the selected compose project.
CID="$(compose ps -q backend 2>/dev/null || true)"
[ -n "$CID" ] || {
  echo "error: backend container not running${INSTANCE_NAME:+ for project '$INSTANCE_NAME'}."
  echo "       start it first:  docker compose ${INSTANCE_NAME:+-p \"$INSTANCE_NAME\" }up -d"
  exit 1
}

REMOTE="/tmp/site-pack-$(date +%s).tar.gz"
echo "[apply-site-pack] copying $(basename "$PACK") into backend container…"
docker cp "$PACK" "$CID:$REMOTE"

# `${arr[@]+"${arr[@]}"}` expands to nothing (not an unbound error) when the array
# is empty under `set -u`, and preserves each element's quoting when it isn't.
echo "[apply-site-pack] importing${PASS_ARGS[*]:+  (${PASS_ARGS[*]})}…"
compose exec -T backend flask --app app.main site import "$REMOTE" ${PASS_ARGS[@]+"${PASS_ARGS[@]}"}

# best-effort cleanup of the copied pack inside the container.
docker exec "$CID" rm -f "$REMOTE" >/dev/null 2>&1 || true

echo "[apply-site-pack] ✅ done."
echo "  Next: this pack carries NO NAP. Set this client's contact info via"
echo "        PATCH /api/admin/site/settings  (or a rebrand) — legalName/phone/email/address/hours."
