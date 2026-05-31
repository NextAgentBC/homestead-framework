# Oracle Site — OpenClaw / Codex Skills

Wrap the backend HTTP API (`backend/app/openapi.json`) as agent skills — the
**"operate the running site"** layer (publish a blog, change the design, redeploy).
Editing the site's *code* (pages, components, styles) is the agent's normal
edit + `docker compose up -d --build` loop, not a skill.

**Single source of truth: this directory.** Don't copy skill content elsewhere — symlink.

## Skills

| Skill | Covers | Auth |
|---|---|---|
| `oracle-site-shared` | base URL, auth/token, conventions, site/health/openapi/login — **read first** | public + admin |
| `oracle-site-blog` | list/read; generate/create/update posts | public + admin |
| `oracle-site-design` | read; update/generate/analyze design profile | public + admin |
| `oracle-site-pages` | create/manage content pages (about, services…) — instant, no rebuild | public + admin |
| `oracle-site-newsletter` | newsletter subscribe, contact form | public |
| `oracle-site-ops` | status/logs/health; redeploy/restart (confirm first) | server shell |

## Configure

```bash
export ORACLE_SITE_API="https://oracle-api.nextagent.ca/api"
export ORACLE_SITE_TOKEN="$(docker compose -f /home/ubuntu/projects/oracle-site/docker-compose.yml \
  exec -T backend flask --app app.main token issue --email you@example.com)"
```

## Activate

OpenClaw **rejects symlinks that escape its skills root** (`symlink-escape`), so **install** these as real directories (re-run with `--force` after editing a skill):

```bash
for d in "$(git rev-parse --show-toplevel)"/skills/oracle-site-*/; do
  openclaw skills install "$d" --force
done
openclaw skills check                          # confirm each shows "ready"
systemctl --user restart openclaw-gateway      # gateway snapshots skills at startup
```

The repo is the source of truth; `install` copies them into `~/.openclaw/workspace/skills/`. Re-install after edits.

**Codex CLI** (optional) reads `~/.codex/skills/` — copy the dirs there too if you use the Codex CLI.
