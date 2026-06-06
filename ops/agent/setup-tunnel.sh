#!/usr/bin/env bash
# Headlessly create + configure a Cloudflare Tunnel for a Homestead deploy.
# No dashboard, no `cloudflared login`, no browser — pure Cloudflare API.
# Idempotent: re-running reuses the tunnel, upserts DNS, recreates the connector.
#
# Required env:
#   CF_API_TOKEN   Cloudflare API token. Scopes: Account › Cloudflare Tunnel › Edit,
#                  Zone › DNS › Edit, Zone › Read.
#   CF_ACCOUNT_ID  Cloudflare account id (dashboard → any domain → right sidebar).
#   SITE_DOMAIN    public hostname for the site   e.g. homestead.example.com
#   API_DOMAIN     public hostname for the API    e.g. homestead-api.example.com
# Optional env:
#   CF_ZONE        the zone (root domain), e.g. example.com  (auto-derived if unset)
#   TUNNEL_NAME    default: homestead
#   EDGE_NET       docker network the connector + app share, default: edge
#   FRONTEND_SVC / BACKEND_SVC  origin services, default the compose aliases.
set -euo pipefail

: "${CF_API_TOKEN:?set CF_API_TOKEN}"
: "${CF_ACCOUNT_ID:?set CF_ACCOUNT_ID}"
: "${SITE_DOMAIN:?set SITE_DOMAIN (e.g. homestead.example.com)}"
: "${API_DOMAIN:?set API_DOMAIN (e.g. homestead-api.example.com)}"
TUNNEL_NAME="${TUNNEL_NAME:-homestead}"
EDGE_NET="${EDGE_NET:-edge}"
FRONTEND_SVC="${FRONTEND_SVC:-http://homestead-site-frontend:3000}"
BACKEND_SVC="${BACKEND_SVC:-http://homestead-site-backend:8000}"
API=https://api.cloudflare.com/client/v4

command -v jq >/dev/null || { echo "need 'jq' (apt-get install -y jq)"; exit 1; }
cf(){ curl -fsS -H "Authorization: Bearer $CF_API_TOKEN" -H "Content-Type: application/json" "$@"; }
ok(){ jq -e '.success==true' >/dev/null 2>&1; }

echo "[tunnel] verifying API token…"
cf "$API/user/tokens/verify" | ok || { echo "  CF_API_TOKEN invalid/expired"; exit 1; }

# 1) tunnel: reuse if it exists, else create a remotely-managed one
echo "[tunnel] ensuring tunnel '$TUNNEL_NAME'…"
tid=$(cf "$API/accounts/$CF_ACCOUNT_ID/cfd_tunnel?name=$TUNNEL_NAME&is_deleted=false" | jq -r '.result[0].id // empty')
if [ -z "$tid" ]; then
  resp=$(cf -X POST "$API/accounts/$CF_ACCOUNT_ID/cfd_tunnel" \
    --data "{\"name\":\"$TUNNEL_NAME\",\"config_src\":\"cloudflare\"}")
  echo "$resp" | ok || { echo "  create failed: $resp"; exit 1; }
  tid=$(echo "$resp" | jq -r '.result.id'); token=$(echo "$resp" | jq -r '.result.token')
else
  token=$(cf "$API/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$tid/token" | jq -r '.result')
fi
[ -n "$tid" ] && [ -n "$token" ] && [ "$token" != "null" ] || { echo "  could not get tunnel id/token"; exit 1; }
echo "[tunnel] id=$tid"

# 2) ingress (remotely-managed config)
echo "[tunnel] writing ingress (site → frontend, api → backend)…"
cf -X PUT "$API/accounts/$CF_ACCOUNT_ID/cfd_tunnel/$tid/configurations" --data @- <<JSON | ok || { echo "  ingress PUT failed"; exit 1; }
{"config":{"ingress":[
  {"hostname":"$SITE_DOMAIN","service":"$FRONTEND_SVC"},
  {"hostname":"$API_DOMAIN","service":"$BACKEND_SVC"},
  {"service":"http_status:404"}
]}}
JSON

# 3) DNS: proxied CNAME hostname → <tid>.cfargotunnel.com  (upsert)
cname="$tid.cfargotunnel.com"
ensure_dns(){
  local host="$1" zone zid rid
  zone="${CF_ZONE:-}"
  if [ -z "$zone" ]; then  # pick the longest zone name that is a suffix of host
    zone=$(cf "$API/zones?account.id=$CF_ACCOUNT_ID&per_page=50" \
      | jq -r --arg h "$host" '.result[] | select($h|endswith("."+.name) or $h==.name) | .name' \
      | awk '{print length, $0}' | sort -rn | head -1 | cut -d' ' -f2-)
  fi
  [ -n "$zone" ] || { echo "  no Cloudflare zone found for $host — set CF_ZONE"; exit 1; }
  zid=$(cf "$API/zones?name=$zone" | jq -r '.result[0].id // empty')
  [ -n "$zid" ] || { echo "  zone '$zone' not found on this account"; exit 1; }
  rid=$(cf "$API/zones/$zid/dns_records?type=CNAME&name=$host" | jq -r '.result[0].id // empty')
  local body="{\"type\":\"CNAME\",\"name\":\"$host\",\"content\":\"$cname\",\"proxied\":true}"
  if [ -n "$rid" ]; then cf -X PUT  "$API/zones/$zid/dns_records/$rid" --data "$body" | ok || { echo "  DNS update failed for $host"; exit 1; }
  else                   cf -X POST "$API/zones/$zid/dns_records"      --data "$body" | ok || { echo "  DNS create failed for $host"; exit 1; }
  fi
  echo "[tunnel] DNS  $host → $cname   (zone $zone)"
}
ensure_dns "$SITE_DOMAIN"
ensure_dns "$API_DOMAIN"

# 4) run the connector on the edge network (so it can reach the app containers)
echo "[tunnel] (re)starting cloudflared connector container…"
docker network create "$EDGE_NET" >/dev/null 2>&1 || true
docker rm -f "${TUNNEL_NAME}-cloudflared" >/dev/null 2>&1 || true
docker run -d --name "${TUNNEL_NAME}-cloudflared" --restart unless-stopped --network "$EDGE_NET" \
  cloudflare/cloudflared:latest tunnel --no-autoupdate run --token "$token" >/dev/null

echo "[tunnel] ✅ done. DNS may take ~1 min to propagate; then run ops/agent/verify.sh."
echo "[tunnel] NOTE: after any 'docker compose up' that RECREATES app containers,"
echo "[tunnel]       run:  docker restart ${TUNNEL_NAME}-cloudflared   (re-resolves new IPs)."
