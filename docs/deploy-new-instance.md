# Deploy a fresh Homestead instance (new server)

Stands up a fully **independent** Homestead — its own database, content, design, and domain —
from this repo. The app's `docker-compose.yml` is self-contained (postgres + backend + frontend);
the only external pieces are an `edge` Docker network and public ingress (a Cloudflare tunnel) + DNS.

## 0. Prereqs (on the target server)

- **Docker + Docker Compose v2 + git.** Any CPU arch — all base images are multi-arch.
- **Two hostnames** you control via Cloudflare: one for the site, one for the API —
  e.g. `mysite.example.com` (frontend) and `mysite-api.example.com` (backend).
- A **Google OAuth Client ID** authorized for the site hostname (for admin login). Optional if you
  only mint admin tokens via CLI (step 6) and don't need browser sign-in.

## 1. Clone

```bash
git clone https://github.com/NextAgentBC/homestead-framework.git homestead
cd homestead
```

## 2. Create the external `edge` network (the tunnel routes through it)

```bash
docker network create edge      # fine if it says it already exists
```

## 3. Configure env — decide your domains FIRST

> The frontend **bakes** `NEXT_PUBLIC_*` at build time. Changing the domain later = rebuild frontend.

**3a. root `.env`** (compose `${}` substitution: postgres creds + frontend build args):

```bash
cat > .env <<'EOF'
POSTGRES_DB=homestead
POSTGRES_USER=homestead
POSTGRES_PASSWORD=CHANGE-ME-strong-password
POSTGRES_PORT=55433
NEXT_PUBLIC_API_BASE_URL=https://mysite-api.example.com/api
NEXT_PUBLIC_SITE_URL=https://mysite.example.com
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-oauth-client-id.apps.googleusercontent.com
EOF
```

**3b. `backend/.env`** (start from the example, then edit):

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` — at minimum:

| var | set to |
|---|---|
| `SECRET_KEY` | a random string — `openssl rand -hex 32` |
| `SITE_NAME` | your brand (shown in the nav) |
| `SITE_URL` | `https://mysite.example.com` |
| `API_PUBLIC_URL` | `https://mysite-api.example.com` |
| `CORS_ORIGINS` | `https://mysite.example.com` |
| `ADMIN_EMAILS` | who may hold an admin token, e.g. `you@example.com` |
| `GOOGLE_CLIENT_ID` | same value as `NEXT_PUBLIC_GOOGLE_CLIENT_ID` (or leave default if CLI-only) |
| `SITE_LOCALES` / `SITE_DEFAULT_LOCALE` | e.g. `en,zh` / `en` |
| `DEEPSEEK_API_KEY` | optional — enables AI blog; without it a deterministic fallback post is used |
| `SMTP_*` | optional — newsletter/contact email |
| `FLASK_ENV` | `production` |

> `DATABASE_URL` in `backend/.env` is **overridden** by compose (it points the backend at the
> `postgres` service automatically), so you can leave that line as-is.

## 4. Build + start (migrations auto-run on boot)

```bash
docker compose up -d --build
docker compose ps
curl -fsS http://127.0.0.1:8000/api/health     # -> {"status":"ok",...}
curl -fsS http://127.0.0.1:3000 -o /dev/null -w '%{http_code}\n'
```

The backend entrypoint runs `flask db upgrade` on start, so the schema is created automatically.

## 5. Public ingress — Cloudflare tunnel (recommended)

Run `cloudflared` on this server **joined to the `edge` network**, routing:

```
mysite.example.com      ->  http://homestead-site-frontend:3000
mysite-api.example.com  ->  http://homestead-site-backend:8000
```

(`homestead-site-frontend` / `homestead-site-backend` are the compose service aliases on `edge`.)
Use a token-based tunnel from the Cloudflare Zero Trust dashboard, or a local config —
see [`../ops/cloudflared/config.yml.example`](../ops/cloudflared/config.yml.example).

> **Deploy gotcha:** every `docker compose up -d --build` (or `up -d`) **recreates** containers →
> new container IPs, but cloudflared caches the old IP and returns **502/530** until it re-resolves.
> **After any recreate, `docker restart <your-cloudflared-container>`**, then verify the **public**
> URL (a local `:8000`/`:3000` 200 does NOT prove the tunnel works).

**Fallback without Cloudflare:** the app already publishes `3000`/`8000`; put your own nginx in
front — see [`../ops/nginx/homestead-site.conf.example`](../ops/nginx/homestead-site.conf.example).

## 6. First admin token (no browser)

```bash
docker compose exec -T backend flask --app app.main token issue --email you@example.com
```

Use it as `Authorization: Bearer <jwt>` for `/api/admin/*` and for the OpenClaw skills. The email
must be in `ADMIN_EMAILS`.

## 7. (Optional) Point OpenClaw skills at this instance

In `homestead-site-shared`, set `HOMESTEAD_SITE_API=https://mysite-api.example.com/api` and mint a token
as above. Then design/compose/blog/media/i18n skills all drive this instance.

## 8. (Optional) Live chat answered by the assistant

A floating chat widget answered by a **sandboxed, tool-less** model turn via OpenClaw, mirrored to
the operator's Telegram, with human take-over. Needs the `openclaw` CLI + a running gateway on the
host (see `docs/openclaw-*`). Full reference: [`ops/webchat-bridge/README.md`](../ops/webchat-bridge/README.md).

**a. Host bridge** (runs on the host, not in Docker — it shells out to `openclaw`):
```bash
cp ops/webchat-bridge/.env.example ops/webchat-bridge/.env   # set WEBCHAT_BRIDGE_TOKEN + WEBCHAT_TG_TARGET (your chat id)
chmod 600 ops/webchat-bridge/.env
cp ops/webchat-bridge/webchat-bridge.service ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now webchat-bridge.service
loginctl enable-linger "$USER"            # survive reboot (same as the gateway)
curl -s http://127.0.0.1:18791/health     # {"ok":true,...}
```

**b. Firewall** — Oracle Cloud Ubuntu REJECTs container→host by default, so allow the bridge port
(idempotent; add to your boot self-heal so it survives reboot):
```bash
sudo iptables -C INPUT -s 172.16.0.0/12 -p tcp --dport 18791 -j ACCEPT 2>/dev/null \
  || sudo iptables -I INPUT 2 -s 172.16.0.0/12 -p tcp --dport 18791 -j ACCEPT
```

**c. Backend env** (`backend/.env`) — the token MUST match the bridge's:
```ini
WEBCHAT_ENABLED=true
WEBCHAT_BRIDGE_URL=http://host.docker.internal:18791
WEBCHAT_BRIDGE_TOKEN=<same as ops/webchat-bridge/.env>
```
`docker-compose.yml` already gives the backend `extra_hosts: host.docker.internal:host-gateway`.
Rebuild backend after editing env: `docker compose up -d --build backend && docker restart tunnel-cloudflared`.

**d. Operator take-over skill** (so the assistant can reply into a thread from Telegram):
```bash
openclaw skills install "$PWD/skills/homestead-site-chat" --force
systemctl --user restart openclaw-gateway
```

**Verify:** `curl -s -X POST https://<api-host>/api/chat -H 'Content-Type: application/json' -d '{"message":"hi"}'`
→ a non-`degraded` reply + a Telegram mirror. Toggle off anytime with `WEBCHAT_ENABLED=false` (backend)
or build the frontend with `NEXT_PUBLIC_WEBCHAT_ENABLED=false`.

## Notes

- **Independent instance:** its own DB, content, and design — nothing shared with other deployments.
- **Volumes** `postgres-data` + `media-data` persist across rebuilds (DB rows + uploaded images survive).
- **No image generator needed.** Switch to your industry — `POST /api/admin/site/rebrand {"industry":"<yours>"}` (or the `homestead-site-rebrand` skill) — and the home/pages fill with a complete layout where every image slot is a **prompt-labelled placeholder**. Replace each with your own uploaded photo (`/api/admin/media`); the on-page prompt says what fits. Generating real images is optional (only if you have a generator).
- **Domain is build-time** for the frontend (step 3a); to change it, rebuild frontend.
- Updates: `git pull` → `docker compose up -d --build` → restart cloudflared (the gotcha above).
