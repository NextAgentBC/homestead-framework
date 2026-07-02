#!/usr/bin/env bash
# Render the whole fleet's health as a single self-contained HTML page you can eyeball
# from a phone or another box. No CDN, no JS framework, no network at view time — just
# inline CSS + the data baked in — so you can `scp` the file anywhere and open it.
#
# It does NOT probe anything itself: the data comes from the fleet status action
#     bash ops/fleet/all.sh status <csv> --json
# (a colleague's ops/fleet/status.sh). This script just paints that JSON. Single source
# of truth for "is it up?" stays in status.sh; this is the window onto it.
#
# Usage:
#   bash ops/fleet/dashboard.sh <instances.csv> [--out <path.html>]
# Defaults:
#   --out  ~/homestead-fleet-status.html
#
# Exit code: non-zero if the status command failed to produce usable JSON (so a cron
# wrapper can tell "couldn't even check" apart from "checked, some sites down").
set -euo pipefail

CSV="${1:-}"
OUT="$HOME/homestead-fleet-status.html"

usage(){
  cat <<'EOF'
usage: bash ops/fleet/dashboard.sh <instances.csv> [--out <path.html>]
  Renders a self-contained HTML health page for every instance in the CSV.
  Data comes from:  bash ops/fleet/all.sh status <csv> --json
  --out   where to write the HTML (default: ~/homestead-fleet-status.html)
EOF
  exit 2
}

[ -n "$CSV" ] || usage
shift || true
while [ "$#" -gt 0 ]; do
  case "$1" in
    --out) OUT="${2:-}"; [ -n "$OUT" ] || usage; shift 2;;
    -h|--help) usage;;
    *) echo "[dashboard] unknown arg: $1"; usage;;
  esac
done
[ -f "$CSV" ] || { echo "[dashboard] csv not found: '$CSV'"; usage; }

# repo root of THIS clone — same derivation as all.sh (script is two levels down).
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ALL_SH="$REPO_ROOT/ops/fleet/all.sh"
[ -f "$ALL_SH" ] || { echo "[dashboard] missing $ALL_SH"; exit 1; }

echo "[dashboard] csv : $CSV"
echo "[dashboard] out : $OUT"

# Pull the fleet status JSON. all.sh prints its own progress banners to stderr-ish lines,
# but --json must emit a clean JSON array on stdout; capture only stdout.
STATUS_JSON="$(bash "$ALL_SH" status "$CSV" --json 2>/dev/null)" || {
  echo "[dashboard] ❌ 'all.sh status <csv> --json' failed."
  echo "            The fleet status action (ops/fleet/status.sh) must exist and print a"
  echo "            JSON array. If a teammate hasn't landed it yet, this dashboard can't render."
  exit 1
}
if [ -z "${STATUS_JSON//[[:space:]]/}" ]; then
  echo "[dashboard] ❌ status command returned no output — nothing to render."
  exit 1
fi

# Render the HTML. The JSON goes in via a FLEET_JSON env var (not stdin, so stdin stays
# free); python3's stdlib json.load does parsing/validation and prints the full doc to
# stdout. All presentation lives in the embedded script below.
#
# Field names + value forms consumed (MUST match status.sh's --json object shape):
#   instance        str   compose project / clone name
#   overall         str   "OK" | "WARN" | "DOWN"  (case-insensitive; unknown -> WARN)
#   publicSite      str   "up" | "down" | "skip"  (skip == no SITE_DOMAIN configured)
#   publicApi       str   "up" | "down" | "skip"  (skip == no API_DOMAIN configured)
#   containers      str   "n/m" running/total, or "n/a" (no docker) / "0/0"
#   pages           int|null  page count from a DB round-trip; null == unknown
#   lastBackupDays  int   days since newest local backup; -1 == none found
#   tunnel          str   "up" | "down" | "n/a"
export FLEET_JSON="$STATUS_JSON"
if ! python3 - > "$OUT.tmp" 2>"$OUT.err" <<'PYEOF'; then
import json, os, sys, html, datetime

raw = os.environ.get("FLEET_JSON", "")
try:
    data = json.loads(raw)
except Exception as e:
    sys.stderr.write("status JSON did not parse: %s\n" % e)
    sys.exit(1)

if isinstance(data, dict):
    # tolerate {"instances": [...]} as well as a bare array
    data = data.get("instances", data.get("fleet", []))
if not isinstance(data, list):
    sys.stderr.write("status JSON must be an array of instance objects\n")
    sys.exit(1)

def esc(v):
    return html.escape("" if v is None else str(v))

def norm(overall):
    s = str(overall or "").strip().upper()
    if s in ("OK", "UP", "GREEN", "HEALTHY"):
        return "OK"
    if s in ("DOWN", "FAIL", "FAILED", "RED", "CRIT", "CRITICAL"):
        return "DOWN"
    if s in ("WARN", "WARNING", "DEGRADED", "YELLOW"):
        return "WARN"
    # unknown / missing -> treat as WARN so it stands out but doesn't read as OK
    return "WARN" if s else "WARN"

def show(v):
    if v is None or v == "":
        return "?"
    return esc(v)

# public probe: "up"/"down"/"skip" -> friendly label
def probe_txt(v):
    s = str(v or "").strip().lower()
    if s == "up":
        return "up"
    if s == "down":
        return "down"
    if s in ("skip", "", "n/a", "na"):
        return "—"
    return esc(v)

def backup_txt(v):
    # status.sh emits -1 for "no backup found"; null/"" also treated as never.
    if v is None or v == "":
        return "never"
    try:
        n = int(v)
        if n < 0:
            return "never"
        return "today" if n == 0 else ("%d day" % n if n == 1 else "%d days" % n)
    except (TypeError, ValueError):
        return esc(v)

rows = []
counts = {"OK": 0, "WARN": 0, "DOWN": 0}
for item in data:
    if not isinstance(item, dict):
        continue
    st = norm(item.get("overall"))
    counts[st] += 1
    rows.append({
        "instance": show(item.get("instance")),
        "state": st,
        "publicSite": probe_txt(item.get("publicSite")),
        "publicApi": probe_txt(item.get("publicApi")),
        "containers": show(item.get("containers")),
        "pages": show(item.get("pages")),
        "backup": backup_txt(item.get("lastBackupDays")),
        "tunnel": show(item.get("tunnel")),
    })

# worst state first (DOWN, then WARN, then OK), then alphabetical — problems float up.
order = {"DOWN": 0, "WARN": 1, "OK": 2}
rows.sort(key=lambda r: (order[r["state"]], r["instance"].lower()))

now = datetime.datetime.now().astimezone()
gen = now.strftime("%Y-%m-%d %H:%M:%S %Z")

if not rows:
    fleet_state = "WARN"
elif counts["DOWN"]:
    fleet_state = "DOWN"
elif counts["WARN"]:
    fleet_state = "WARN"
else:
    fleet_state = "OK"

card_html = []
for r in rows:
    card_html.append(
        '<article class="card {sc}">'
        '<header class="chead"><span class="dot"></span>'
        '<h2>{inst}</h2><span class="badge {sc}">{st}</span></header>'
        '<dl class="metrics">'
        '<div><dt>Site</dt><dd>{site}</dd></div>'
        '<div><dt>API</dt><dd>{api}</dd></div>'
        '<div><dt>Containers</dt><dd>{cont}</dd></div>'
        '<div><dt>Pages</dt><dd>{pages}</dd></div>'
        '<div><dt>Last backup</dt><dd>{bk}</dd></div>'
        '<div><dt>Tunnel</dt><dd>{tun}</dd></div>'
        '</dl></article>'.format(
            sc=r["state"].lower(), inst=r["instance"], st=r["state"],
            site=r["publicSite"], api=r["publicApi"], cont=r["containers"],
            pages=r["pages"], bk=r["backup"], tun=r["tunnel"],
        )
    )

cards = "\n".join(card_html) if card_html else \
    '<p class="empty">No instances found in the status output.</p>'

summary = ('%d OK &middot; %d WARN &middot; %d DOWN'
           % (counts["OK"], counts["WARN"], counts["DOWN"]))

doc = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="900">
<title>Homestead fleet status</title>
<style>
  :root {{
    --bg:#f4f5f7; --fg:#1c2128; --muted:#5b6570; --card:#ffffff; --line:#e2e5e9;
    --ok:#1a7f37; --ok-bg:#e6f4ea; --warn:#9a6700; --warn-bg:#fff5d6;
    --down:#cf222e; --down-bg:#ffe3e3;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --card:#161b22; --line:#30363d;
      --ok:#3fb950; --ok-bg:#12261a; --warn:#d29922; --warn-bg:#2b2412;
      --down:#f85149; --down-bg:#2b1416;
    }}
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; padding:1.5rem; background:var(--bg); color:var(--fg);
    font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }}
  header.top {{ max-width:1100px; margin:0 auto 1.25rem; }}
  header.top h1 {{ margin:0 0 .25rem; font-size:1.5rem; display:flex; align-items:center; gap:.5rem; flex-wrap:wrap; }}
  .fleetbadge {{ font-size:.8rem; font-weight:700; padding:.15rem .55rem; border-radius:999px; letter-spacing:.03em; }}
  .fleetbadge.ok {{ color:var(--ok); background:var(--ok-bg); }}
  .fleetbadge.warn {{ color:var(--warn); background:var(--warn-bg); }}
  .fleetbadge.down {{ color:var(--down); background:var(--down-bg); }}
  .sub {{ color:var(--muted); font-size:.85rem; }}
  .grid {{
    max-width:1100px; margin:0 auto; display:grid; gap:1rem;
    grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
  }}
  .card {{
    background:var(--card); border:1px solid var(--line); border-left-width:5px;
    border-radius:10px; padding:.9rem 1rem;
  }}
  .card.ok {{ border-left-color:var(--ok); }}
  .card.warn {{ border-left-color:var(--warn); }}
  .card.down {{ border-left-color:var(--down); }}
  .chead {{ display:flex; align-items:center; gap:.5rem; margin-bottom:.6rem; }}
  .chead h2 {{ margin:0; font-size:1rem; font-weight:600; flex:1; overflow-wrap:anywhere; }}
  .dot {{ width:.7rem; height:.7rem; border-radius:50%; flex:0 0 auto; }}
  .card.ok .dot {{ background:var(--ok); }}
  .card.warn .dot {{ background:var(--warn); }}
  .card.down .dot {{ background:var(--down); }}
  .badge {{ font-size:.7rem; font-weight:700; padding:.1rem .45rem; border-radius:999px; letter-spacing:.03em; }}
  .badge.ok {{ color:var(--ok); background:var(--ok-bg); }}
  .badge.warn {{ color:var(--warn); background:var(--warn-bg); }}
  .badge.down {{ color:var(--down); background:var(--down-bg); }}
  dl.metrics {{ display:grid; grid-template-columns:1fr 1fr; gap:.4rem .8rem; margin:0; }}
  dl.metrics div {{ display:flex; flex-direction:column; }}
  dl.metrics dt {{ font-size:.7rem; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }}
  dl.metrics dd {{ margin:0; font-size:.95rem; font-weight:600; overflow-wrap:anywhere; }}
  .empty {{ max-width:1100px; margin:0 auto; color:var(--muted); }}
  footer.legend {{
    max-width:1100px; margin:1.5rem auto 0; padding-top:1rem; border-top:1px solid var(--line);
    color:var(--muted); font-size:.8rem; display:flex; gap:1.25rem; flex-wrap:wrap; align-items:center;
  }}
  footer.legend .k {{ display:inline-flex; align-items:center; gap:.4rem; }}
  footer.legend .sw {{ width:.7rem; height:.7rem; border-radius:50%; display:inline-block; }}
  footer.legend .sw.ok {{ background:var(--ok); }}
  footer.legend .sw.warn {{ background:var(--warn); }}
  footer.legend .sw.down {{ background:var(--down); }}
</style>
</head>
<body>
<header class="top">
  <h1>Homestead fleet status <span class="fleetbadge {fleet_lc}">{fleet}</span></h1>
  <div class="sub">Generated {gen} &nbsp;&middot;&nbsp; {summary} &nbsp;&middot;&nbsp; auto-refreshes every 15 min</div>
</header>
<main class="grid">
{cards}
</main>
<footer class="legend">
  <span class="k"><span class="sw ok"></span>OK — site + API + containers + tunnel all healthy</span>
  <span class="k"><span class="sw warn"></span>WARN — degraded / stale backup / unknown</span>
  <span class="k"><span class="sw down"></span>DOWN — site or API unreachable</span>
</footer>
</body>
</html>
""".format(
    fleet=fleet_state, fleet_lc=fleet_state.lower(),
    gen=esc(gen), summary=summary, cards=cards,
)

sys.stdout.write(doc)
PYEOF
  echo "[dashboard] ❌ could not render HTML from the status JSON:"
  sed 's/^/            /' "$OUT.err" >&2 || true
  rm -f "$OUT.tmp" "$OUT.err"
  exit 1
fi
rm -f "$OUT.err"
mv "$OUT.tmp" "$OUT"
echo "[dashboard] ✅ wrote $OUT"
