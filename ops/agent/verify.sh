#!/usr/bin/env bash
# Verify a Homestead deploy: local origin health + PUBLIC reachability through the tunnel.
# Exits non-zero if anything isn't reachable — so an agent can branch on it.
# Required env: SITE_DOMAIN API_DOMAIN
set -u
: "${SITE_DOMAIN:?set SITE_DOMAIN}"; : "${API_DOMAIN:?set API_DOMAIN}"
fail=0
check(){ # url  expected-codes(space-sep)
  local code; code=$(curl -s -o /dev/null -m 20 -w '%{http_code}' "$1")
  if printf ' %s ' $2 | grep -q " $code "; then echo "  OK   $code  $1"
  else echo "  BAD  $code  $1  (want: $2)"; fail=1; fi
}
echo "[verify] local origin (published ports):"
check "http://127.0.0.1:8000/api/health" "200"
check "http://127.0.0.1:3000/"           "200 307 308"
echo "[verify] public (through the Cloudflare tunnel):"
check "https://$API_DOMAIN/api/health"   "200"
check "https://$SITE_DOMAIN/"            "200 301 307 308"
if [ "$fail" = 0 ]; then echo "[verify] ✅ deploy looks healthy — site is live."; else
  echo "[verify] ❌ not fully reachable. If local is OK but public is 502/530:"
  echo "         1) DNS may still be propagating (wait ~1 min)."
  echo "         2) after any container recreate: docker restart <tunnel>-cloudflared"
  exit 1
fi
