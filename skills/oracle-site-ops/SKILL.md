---
name: oracle-site-ops
description: "Operate the running Oracle Site deployment on the server: status, logs, health, redeploy, restart (docker compose). Triggers: '网站状态 / 容器状态', 'site status', '看网站日志 / 日志', 'site logs', '重新部署 / 重部署 / 重新构建网站', 'redeploy / rebuild the site', '重启网站 / 重启后端', 'restart the site'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - docker
---

# Oracle Site — Ops (deploy / status)

> Prerequisite: `../oracle-site-shared/SKILL.md`. Run these on the server, in the deploy dir:
> `cd /home/ubuntu/projects/oracle-site`

## Read-only (safe — run without asking)

```bash
docker compose ps                          # container status
docker compose logs --tail 50 backend      # or: frontend / postgres
curl -s "$ORACLE_SITE_API/health"          # app readiness
```

## State-changing (CONFIRM FIRST)

**Always state what will happen and get an explicit "yes" in chat before running these — they rebuild or restart the live site.**

```bash
docker compose up -d --build               # redeploy after code/env changes (rebuilds images)
docker restart tunnel-cloudflared          # REQUIRED after any recreate (see below)
docker compose restart backend             # or frontend — restart one service (keeps the IP, no tunnel restart needed)
```

**Cloudflare tunnel gotcha — always restart cloudflared after a recreate.** The
infra tunnel routes `homestead.* / homestead-api.*` to the `oracle-site-frontend /
-backend` aliases on the `edge` network. When `up -d --build` (or `up -d`)
**recreates** a container it gets a new IP, but cloudflared caches the old one and
returns **502/530** until it re-resolves. So after any recreate, run
`docker restart tunnel-cloudflared` (briefly blips other tunneled apps too) and
re-check the public URL. A plain `restart` (not recreate) keeps the IP — no tunnel
restart needed.

Rules:
- Read-only commands (`ps`, `logs`, health): run freely.
- `up --build` / `restart` / anything that stops or rebuilds: confirm first.
- Never run `down`, `rm`, or delete volumes from this skill.
- After a redeploy: `docker restart tunnel-cloudflared`, then verify `docker compose ps`
  + `curl -fsS https://homestead.nextagent.ca/en` (the **public** URL, not just local health —
  local 200 doesn't prove the tunnel works).
