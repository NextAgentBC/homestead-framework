# Deployment Guide

> **This deployment (Homestead)** runs everything via Docker Compose in
> `/home/ubuntu/projects/homestead-site` (the `main` checkout) behind one shared Cloudflare Tunnel.
> The box below is the concrete production runbook; the sections after it explain the general
> tunnel / nginx options for the lecture.

## Production deploy (Docker Compose)

```bash
# from /home/ubuntu/projects/homestead-site, on the `main` checkout
docker compose up -d --build            # build + (re)create frontend & backend
docker restart tunnel-cloudflared       # REQUIRED after any recreate — see gotcha
docker compose ps
curl -fsS https://your-api.example.com/api/health
```

- **Tunnel gotcha (the #1 deploy footgun):** `up -d --build` *recreates* containers → new container
  IPs, but `tunnel-cloudflared` caches the old IP and returns **502/530** until it re-resolves.
  **Always `docker restart tunnel-cloudflared` after a recreate**, then verify the **public** URL
  (a local `:8000` 200 does NOT prove the tunnel works). The tunnel routes by network alias on the
  external `edge` network: `homestead.* → homestead-site-frontend:3000`, `homestead-api.* → homestead-site-backend:8000`.
- **Migrations run automatically:** `backend/docker-entrypoint.sh` runs `flask db upgrade` on start,
  so a new migration applies on container boot (a bad migration crash-loops the backend).
- **Back up Postgres before any migration:**
  `docker compose exec -T postgres pg_dump -U homestead_site homestead_site > ~/backups/homestead_site_$(date +%F).sql`
- **Media** is a named volume (`media-data:/app/media`) — uploaded images survive rebuilds.
- **OpenClaw skills:** after editing a `skills/homestead-site-*` skill, reinstall it
  (`openclaw skills install <ABSOLUTE-path> --force`) then `systemctl --user restart openclaw-gateway`
  (it snapshots skills at startup).

Public URLs: `https://your-site.example.com` (frontend) · `https://your-api.example.com/api` (backend).

---

## Recommended: Cloudflare Tunnel

Use Cloudflare Tunnel for the lecture framework.

Why:

- Students do not need to expose Oracle VM ports 80/443.
- TLS is handled by Cloudflare.
- The public IP can remain private from normal visitors.
- Domain routing is repeatable: `example.com` -> Next.js, `api.example.com` -> Flask.

Basic shape:

```text
Cloudflare DNS
  example.com      -> tunnel -> localhost:3000
  api.example.com  -> tunnel -> localhost:8000
Oracle VM
  nextjs service on 127.0.0.1:3000
  flask service on 127.0.0.1:8000
```

See `ops/cloudflared/config.yml.example`.

## Fallback: Static IP + Nginx

Use this when you explicitly want students to learn classic DNS and reverse proxy.

```text
Cloudflare DNS A record -> Oracle static IP
Nginx
  /      -> localhost:3000
  /api/  -> localhost:8000
```

See `ops/nginx/homestead-site.conf.example`.

## Daily Blog Job

Run once per day:

```bash
cd /opt/homestead-site/backend
. .venv/bin/activate
flask --app app.main blog generate-daily
```

Use `ops/systemd/homestead-blog.timer` and `ops/systemd/homestead-blog.service`.

