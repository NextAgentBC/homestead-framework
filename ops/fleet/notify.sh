#!/usr/bin/env bash
# Fleet alerting: run status, and if ANY instance is WARN/DOWN, push a compact Telegram
# summary to the operator. All-OK is silent (so a 15-min cron doesn't nag) unless --always.
#
# Like dashboard.sh, this does NOT probe anything itself — it consumes
#     bash ops/fleet/all.sh status <csv> --json
# (a colleague's ops/fleet/status.sh) so "is it up?" has one source of truth.
#
# Usage:
#   bash ops/fleet/notify.sh <instances.csv> [--always]
#     --always   send the summary even when everything is OK (heartbeat)
#
# Telegram config (env; same Bot API shape as ops/webchat-bridge):
#   TELEGRAM_BOT_TOKEN   bot token from @BotFather
#   TELEGRAM_CHAT_ID     operator chat/group id to post to
# If EITHER is unset, the summary is printed to stdout and the script exits 0 — so it's
# still useful as a plain cron log line on hosts without a bot configured.
#
# Exit code:
#   0  ran fine (sent, printed, or silently-OK)
#   1  couldn't get usable status JSON (status.sh missing / broke) — a real "can't check".
set -euo pipefail

CSV="${1:-}"
ALWAYS=0

usage(){
  cat <<'EOF'
usage: bash ops/fleet/notify.sh <instances.csv> [--always]
  Runs the fleet status and Telegram-pings the operator only when something is WARN/DOWN.
  --always   also send when all instances are OK (a heartbeat/"still watching" ping)
  Data comes from:  bash ops/fleet/all.sh status <csv> --json
  Telegram via env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (unset -> print to stdout, exit 0)
EOF
  exit 2
}

[ -n "$CSV" ] || usage
shift || true
while [ "$#" -gt 0 ]; do
  case "$1" in
    --always) ALWAYS=1; shift;;
    -h|--help) usage;;
    *) echo "[notify] unknown arg: $1"; usage;;
  esac
done
[ -f "$CSV" ] || { echo "[notify] csv not found: '$CSV'"; usage; }

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ALL_SH="$REPO_ROOT/ops/fleet/all.sh"
[ -f "$ALL_SH" ] || { echo "[notify] missing $ALL_SH"; exit 1; }

STATUS_JSON="$(bash "$ALL_SH" status "$CSV" --json 2>/dev/null)" || {
  echo "[notify] ❌ 'all.sh status <csv> --json' failed — the fleet status action"
  echo "         (ops/fleet/status.sh) must exist and print a JSON array."
  exit 1
}
if [ -z "${STATUS_JSON//[[:space:]]/}" ]; then
  echo "[notify] ❌ status command returned no output — nothing to check."
  exit 1
fi

# python3 distills the JSON into a plain-text alert body and tells us (via exit code)
# whether anything is wrong: exit 0 = has WARN/DOWN, exit 3 = all OK, exit 1 = bad JSON.
# The message text goes to stdout so bash can capture it.
export FLEET_JSON="$STATUS_JSON"
set +e
MSG="$(python3 - <<'PYEOF'
import json, os, sys

raw = os.environ.get("FLEET_JSON", "")
try:
    data = json.loads(raw)
except Exception as e:
    sys.stderr.write("status JSON did not parse: %s\n" % e)
    sys.exit(1)
if isinstance(data, dict):
    data = data.get("instances", data.get("fleet", []))
if not isinstance(data, list):
    sys.stderr.write("status JSON must be an array of instance objects\n")
    sys.exit(1)

def norm(v):
    s = str(v or "").strip().upper()
    if s in ("OK", "UP", "GREEN", "HEALTHY"):
        return "OK"
    if s in ("DOWN", "FAIL", "FAILED", "RED", "CRIT", "CRITICAL"):
        return "DOWN"
    return "WARN"  # WARN/unknown/missing

def s(v):
    return "?" if v is None or v == "" else str(v)

# Collect, per non-OK instance, the specific problem items so the ping is actionable.
# Value forms come straight from status.sh: publicSite/publicApi are "up"/"down"/"skip";
# containers is "n/m"/"n/a"/"0/0"; tunnel is "up"/"down"/"n/a"; lastBackupDays is an int
# with -1 == none found.
def problems(it):
    out = []
    if str(it.get("publicSite") or "").strip().lower() == "down":
        out.append("site down")
    if str(it.get("publicApi") or "").strip().lower() == "down":
        out.append("api down")
    cont = s(it.get("containers"))
    if "/" in cont:
        try:
            run, exp = cont.split("/", 1)
            if int(run) < int(exp):
                out.append("containers %s" % cont)
        except ValueError:
            pass
    if str(it.get("tunnel") or "").strip().lower() == "down":
        out.append("tunnel down")
    bk = it.get("lastBackupDays")
    try:
        n = int(bk)
        if n < 0:
            out.append("no backup")
        elif n >= 2:
            out.append("backup %dd old" % n)
    except (TypeError, ValueError):
        if bk is None or bk == "":
            out.append("no backup")
    return out

counts = {"OK": 0, "WARN": 0, "DOWN": 0}
bad = []
for it in data:
    if not isinstance(it, dict):
        continue
    st = norm(it.get("overall"))
    counts[st] += 1
    if st != "OK":
        name = s(it.get("instance"))
        detail = ", ".join(problems(it)) or st.lower()
        bad.append((st, name, detail))

order = {"DOWN": 0, "WARN": 1}
bad.sort(key=lambda b: (order.get(b[0], 2), b[1].lower()))

header = "Homestead fleet: %d OK / %d WARN / %d DOWN" % (
    counts["OK"], counts["WARN"], counts["DOWN"])

if bad:
    lines = [("[DOWN] " if st == "DOWN" else "[WARN] ") + "%s — %s" % (name, detail)
             for st, name, detail in bad]
    sys.stdout.write("⚠️ " + header + "\n" + "\n".join(lines))
    sys.exit(0)   # something is wrong -> caller should send
else:
    sys.stdout.write("✅ " + header + " — all instances healthy")
    sys.exit(3)   # all OK -> caller stays silent unless --always
PYEOF
)"
RC=$?
set -e

if [ "$RC" -eq 1 ]; then
  echo "[notify] ❌ could not interpret the status JSON."
  exit 1
fi

# RC 0 = has problems (send); RC 3 = all OK (send only if --always).
if [ "$RC" -eq 3 ] && [ "$ALWAYS" -ne 1 ]; then
  echo "[notify] ✅ all instances OK — staying silent (use --always to force a heartbeat)."
  exit 0
fi

# No bot configured? Print and exit 0 — usable as a cron log line without Telegram.
if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "[notify] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — printing summary instead:"
  printf '%s\n' "$MSG"
  exit 0
fi

# Push to Telegram Bot API (same shape as the webchat-bridge mirror). --data-urlencode
# keeps newlines/emoji intact; -sS surfaces curl errors without a progress bar.
HTTP="$(curl -sS -o /dev/null -m 20 -w '%{http_code}' \
  "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text=${MSG}" \
  --data-urlencode "disable_web_page_preview=true" || echo "000")"

if [ "$HTTP" = "200" ]; then
  echo "[notify] ✅ Telegram alert sent (HTTP $HTTP)."
  exit 0
else
  echo "[notify] ⚠️  Telegram send returned HTTP $HTTP — summary was:"
  printf '%s\n' "$MSG"
  # Non-fatal on purpose: the status check itself succeeded; delivery is best-effort so a
  # transient Telegram/API hiccup doesn't flip the cron unit to 'failed'.
  exit 0
fi
