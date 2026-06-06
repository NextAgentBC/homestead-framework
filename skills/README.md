# Homestead — OpenClaw / Codex Skills

Wrap the backend HTTP API (`backend/app/openapi.json`) as agent skills — the
**"operate the running site"** layer (publish a blog, change the design, redeploy).
Editing the site's *code* (pages, components, styles) is the agent's normal
edit + `docker compose up -d --build` loop, not a skill.

**Single source of truth: this directory.** Don't copy skill content elsewhere — symlink.

## Skills

| Skill | Covers | Auth |
|---|---|---|
| `website` | **control center** — the categorized `/website` menu (content / design / language / ops); routes to the skills below | — |
| `homestead-site-shared` | base URL, auth/token, conventions, locales, site/health/openapi/login — **read first** | public + admin |
| `homestead-site-blog` | list/read; generate/create/update posts | public + admin |
| `homestead-site-design` | read; update/generate/analyze design profile (18 presets + image-ready industry templates) | public + admin |
| `homestead-site-rebrand` | **switch the whole site to a new industry** in one atomic call, then loop on the consistency audit until coherent (`/admin/site/rebrand` · `/admin/consistency`) | public + admin |
| `homestead-site-compose` | block-level page editing (add/move/edit/remove/batch), locale-aware | public + admin |
| `homestead-site-capture` | rebuild a section from a screenshot → flexible `section` block + `/patterns` library | public + admin |
| `homestead-site-i18n` | translate content + UI chrome (path-based `/zh`) — the agent is the translator | public + admin |
| `homestead-site-pages` | create/manage content pages (about, services…) — instant, no rebuild | public + admin |
| `homestead-site-newsletter` | newsletter subscribe, contact form | public |
| `homestead-site-media` | upload-only image hosting (multipart / url / base64) → absolute URLs for blocks & blog | public + admin |
| `homestead-site-history` | edit history — list revisions, undo last change, restore a kept snapshot | admin |
| `homestead-site-chat` | live website chat — list/read conversations, take over and reply | admin |
| `homestead-site-ops` | status/logs/health; redeploy/restart (confirm first) | server shell |

Plus one thin trigger skill per block type (`homestead-site-block-*`), generated from the
live catalog by `generate-block-skills.py` — they delegate to `homestead-site-compose`.

## Configure

```bash
export HOMESTEAD_SITE_API="https://your-api.example.com/api"
export HOMESTEAD_SITE_TOKEN="$(docker compose -f /home/ubuntu/projects/homestead-site/docker-compose.yml \
  exec -T backend flask --app app.main token issue)"   # no --email → uses the configured admin
```

## Activate

OpenClaw **rejects symlinks that escape its skills root** (`symlink-escape`), so **install** these as real directories (re-run with `--force` after editing a skill):

```bash
# Core website skills (each becomes a Telegram command). The per-block trigger
# skills (homestead-site-block-*) are OPTIONAL — compose/capture already cover every
# block type, so they're skipped by default to keep the command menu clean.
for d in "$(git rev-parse --show-toplevel)"/skills/*/; do
  case "$d" in */homestead-site-block-*/) continue ;; esac
  openclaw skills install "$d" --force
done
openclaw skills check                          # confirm each shows "ready"
systemctl --user restart openclaw-gateway      # gateway snapshots skills at startup
```

OpenClaw auto-exposes every installed skill as a Telegram slash command
(`homestead-site-blog` → `/homestead_site_blog`, `website` → `/website`). **`/website`**
is the categorized front door — start there. Want per-block commands
(`/homestead_site_block_pricing` …)? Install `skills/homestead-site-block-*` explicitly.

The repo is the source of truth; `install` copies them into `~/.openclaw/workspace/skills/`. Re-install after edits.

**Codex CLI** (optional) reads `~/.codex/skills/` — copy the dirs there too if you use the Codex CLI.
