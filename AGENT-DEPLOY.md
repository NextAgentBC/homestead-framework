# Deploy Homestead with an AI agent (OpenClaw / Codex)

**Hand this file to your agent.** It stands up a fully independent Homestead instance
(its own database, content, design, domain) end-to-end, headless — no dashboard clicking.

The agent is good at deterministic, idempotent, self-verifying steps. The few things it
**cannot** do itself are called out as **🧑 HUMAN** — gather those first.

---

## 0. 🧑 HUMAN — provide these once, then let the agent run

The agent will ask you to paste these. Have them ready:

| value | what it is / where to get it |
|---|---|
| **a server** | a Linux box with **Docker + Docker Compose v2 + git**, that the agent can run shell on. Any CPU arch. |
| `SITE_DOMAIN` | the site hostname, e.g. `homestead.example.com` |
| `API_DOMAIN` | the API hostname, e.g. `homestead-api.example.com` |
| `CF_API_TOKEN` | Cloudflare API token — scopes **Account › Cloudflare Tunnel › Edit**, **Zone › DNS › Edit**, **Zone › Read**. (dash.cloudflare.com → My Profile → API Tokens → Create Token) |
| `CF_ACCOUNT_ID` | Cloudflare account id (dashboard → pick any domain → right sidebar) |
| `ADMIN_EMAIL` | who may hold an admin token, e.g. `you@example.com` |
| *(optional)* `GOOGLE_CLIENT_ID` | only if you want **browser** admin login. Skip it — the agent can mint an admin token via CLI. Authorize the origin `https://SITE_DOMAIN` in Google Cloud Console if you do use it. |
| *(optional)* `DEEPSEEK_API_KEY` | enables the AI blog generator. Without it, a deterministic fallback post is used. |

> The **domain must be a zone on this Cloudflare account** (the token's account). The agent
> creates the tunnel + DNS for you — you do **not** touch the Cloudflare dashboard.

---

## 1. 🤖 AGENT — preflight (fail fast, before changing anything)

```bash
git clone https://github.com/NextAgentBC/homestead-framework.git homestead && cd homestead

# tools
for b in docker git jq openssl curl; do command -v "$b" >/dev/null || { echo "MISSING: $b"; MISS=1; }; done
docker compose version >/dev/null 2>&1 || { echo "MISSING: docker compose v2"; MISS=1; }
[ "${MISS:-}" ] && { echo "Install the missing tools, then re-run."; exit 1; }   # 🧑 ask human if unsure

# required values present?  (export them in this shell first)
: "${SITE_DOMAIN:?}"; : "${API_DOMAIN:?}"; : "${CF_API_TOKEN:?}"; : "${CF_ACCOUNT_ID:?}"; : "${ADMIN_EMAIL:?}"

# is the Cloudflare token valid?
curl -fsS -H "Authorization: Bearer $CF_API_TOKEN" \
  https://api.cloudflare.com/client/v4/user/tokens/verify | grep -q '"status":"active"' \
  && echo "CF token OK" || { echo "🧑 CF_API_TOKEN invalid — get a fresh one."; exit 1; }
```

If anything is missing, **STOP and ask the human** — do not guess.

## 2. 🤖 AGENT — configure env (secrets auto-generated)

```bash
export SITE_DOMAIN API_DOMAIN ADMIN_EMAIL
export SITE_NAME="My Site"          # optional, default Homestead
export SITE_LOCALES="en,zh"         # optional, default en
# export GOOGLE_CLIENT_ID=...  DEEPSEEK_API_KEY=...   # optional
bash ops/agent/make-env.sh          # writes .env + backend/.env, generates SECRET_KEY + DB password
```

## 3. 🤖 AGENT — build + start (migrations run automatically on boot)

```bash
docker network create edge 2>/dev/null || true
docker compose up -d --build
# wait for the backend to be healthy
for i in $(seq 1 60); do
  docker compose exec -T backend python -c "import urllib.request as u;u.urlopen('http://localhost:8000/api/health',timeout=3)" 2>/dev/null && break
  sleep 3
done
```

## 4. 🤖 AGENT — public ingress (Cloudflare tunnel, fully scripted)

```bash
export CF_API_TOKEN CF_ACCOUNT_ID SITE_DOMAIN API_DOMAIN
export TUNNEL_NAME="homestead"      # optional; pick a unique name per instance
bash ops/agent/setup-tunnel.sh      # creates tunnel + ingress + DNS via the CF API, runs the connector
```

## 5. 🤖 AGENT — verify (this is the success gate)

```bash
sleep 30                            # let DNS propagate
SITE_DOMAIN="$SITE_DOMAIN" API_DOMAIN="$API_DOMAIN" bash ops/agent/verify.sh
```

`verify.sh` exits **non-zero** if the site isn't publicly reachable. If local origin is fine
but public is 502/530: wait a minute (DNS), or `docker restart ${TUNNEL_NAME}-cloudflared`,
then re-run verify. **Do not report success until verify passes.**

## 6. 🤖 AGENT — first admin token, then report

```bash
docker compose exec -T backend flask --app app.main token issue --email "$ADMIN_EMAIL"
```

Report back to the human:
- ✅ `https://SITE_DOMAIN` is live (verify passed)
- the admin token (for `Authorization: Bearer <jwt>` and the OpenClaw skills)
- to drive the site by chat: point `homestead-site-shared`'s `HOMESTEAD_SITE_API` at `https://API_DOMAIN/api`

---

## Notes & guarantees for the agent

- **Idempotent.** Re-running any step is safe: `make-env.sh` rewrites env, `setup-tunnel.sh`
  reuses the tunnel + upserts DNS, `compose up -d` reconciles.
- **The cloudflared gotcha.** Any `docker compose up -d --build` that **recreates** the app
  containers gives them new IPs; afterwards run `docker restart ${TUNNEL_NAME}-cloudflared`.
- **Domain is build-time** for the frontend (baked from `.env`). To change it: edit `.env`,
  `docker compose up -d --build frontend`, restart the tunnel.
- **Updates:** `git pull && docker compose up -d --build && docker restart ${TUNNEL_NAME}-cloudflared`.
- **No-tunnel fallback:** the app also publishes ports `3000`/`8000`; front it with your own
  nginx (`ops/nginx/homestead-site.conf.example`) if you'd rather not use Cloudflare.
- Full human reference: [`docs/deploy-new-instance.md`](docs/deploy-new-instance.md) · contract: [`docs/api-contract.md`](docs/api-contract.md).
