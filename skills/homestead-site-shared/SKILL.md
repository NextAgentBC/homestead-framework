---
name: homestead-site-shared
description: "Homestead (the website framework) API basics + auth + capability map — READ FIRST. Base URL, admin token issuance, conventions, the whole API/theme/block surface at a glance, plus site config, health, OpenAPI, Google login. Triggers: 'homestead / 网站 API', 'site health 状态', '拿/签发 admin token', 'admin token', '网站信息 / site info', 'openapi 契约', '网站有哪些能力 / api 清单'."
metadata:
  version: 0.2.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Homestead — Shared Reference (read first)

Wraps the framework's HTTP API (full contract: `GET $HOMESTEAD_SITE_API/openapi.json`).
Public endpoints need no auth; admin endpoints need an admin bearer token.

## Configure

```bash
export HOMESTEAD_SITE_API="https://your-api.example.com/api"   # this deployment's API base
```

Public routes: `$HOMESTEAD_SITE_API/...` (e.g. `/blogs`). Admin routes: `$HOMESTEAD_SITE_API/admin/...`.

The `HOMESTEAD_SITE_API` / `HOMESTEAD_SITE_TOKEN` pair above is the **single-site** shortcut.
When one operator runs several sites, don't juggle those by hand — use the registry below.

## 多站运营(site registry)

一个 operator 常常同时管好几个客户站。约定一个注册表把"站名 → api/token/目录"记在一处,
技能每次动手前先**确定当前是哪个站**,再从注册表取该站的 `api` / `token` / `dir`。

**注册表:`~/.homestead/sites.json`**

```json
{
  "acme":   { "api": "https://acme-api.example.com/api",   "token": "<jwt>", "dir": "/home/ubuntu/projects/homestead-acme" },
  "globex": { "api": "https://globex-api.example.com/api", "token": "<jwt>", "dir": "/home/ubuntu/projects/homestead-globex" }
}
```

- `api` → export 成 `HOMESTEAD_SITE_API`(所有公开/admin 路由的基址)。
- `token` → export 成 `HOMESTEAD_SITE_TOKEN`(admin 路由的 Bearer;失效就按上面的 "Auth" 用该站
  的 `dir` 重签一枚,写回注册表)。
- `dir` → 该站 clone 目录,即上面 Auth 用的 `$HOMESTEAD_SITE_DIR`(签 token / 跑 compose 都在这)。

**确定"当前站"的顺序**:① 用户在本轮点名了哪个站(如"给 acme 加篇博客")→ 用它;② 否则
用上次用过的站(会话里最近一次选定的);③ 都没有且注册表只有一个站 → 用那个;④ 有多个又
没线索 → **先问用户是哪个站**,别乱猜(改错站是事故)。

**选定后加载它**(jq 从注册表取值,一次性 export 三样):

```bash
site="acme"                                   # 第①/②/③步定下来的站名
cfg=~/.homestead/sites.json
export HOMESTEAD_SITE_API="$(jq -r --arg s "$site" '.[$s].api'   "$cfg")"
export HOMESTEAD_SITE_TOKEN="$(jq -r --arg s "$site" '.[$s].token' "$cfg")"
export HOMESTEAD_SITE_DIR="$(jq -r --arg s "$site" '.[$s].dir'   "$cfg")"
```

单站场景无需注册表:直接 export `HOMESTEAD_SITE_API`(和需要时 `HOMESTEAD_SITE_TOKEN` /
`HOMESTEAD_SITE_DIR`)即可,一切照旧。运维侧按站批量跑 update/verify/backup 见 `ops/fleet/`。

## Auth (admin token)

Admin routes require `Authorization: Bearer <jwt>`. Two ways to get one:

1. **Interactive (browser):** Google Sign-In on the site (`POST /auth/google`).
2. **Non-interactive (agents — no browser):** run where the backend runs, pointing at the
   *current* site's clone directory (`$HOMESTEAD_SITE_DIR`, or the `dir` from the registry —
   see "多站运营" below). Never hard-code a single path once more than one site exists:

```bash
: "${HOMESTEAD_SITE_DIR:?set to the current site's clone dir, e.g. /home/ubuntu/projects/homestead-<name>}"
export HOMESTEAD_SITE_TOKEN="$(docker compose -f "$HOMESTEAD_SITE_DIR/docker-compose.yml" \
  exec -T backend flask --app app.main token issue)"
```

With **no `--email`** it uses the first `ADMIN_EMAILS` entry (the admin) — most robust. Pass
`--email <x>` only if `x` is actually in the backend's `ADMIN_EMAILS`, else it's rejected.
`--days N` overrides lifetime (default 168h).

## Conventions

- JSON in/out. Single object → `{"item": {...}}`, list → `{"items": [...]}`.
- Errors → `{"error": {"code","message"}}` (401 missing/bad token, 403 not admin, 404 not found).
- Send `-H "Content-Type: application/json"` on POST/PATCH.
- Edits are **instant** (design / compose / i18n / media writes need no redeploy).
- **Locales (i18n):** `GET /site` → `locales` + `defaultLocale`. Read localized content with
  `?locale=zh` on `/design`, `/pages*`, `/blogs*`; write it with `?locale=zh` on the matching
  admin routes (content goes into that locale's overlay, default columns untouched). UI chrome
  strings: `GET /i18n/<locale>`, `PATCH /admin/i18n/<locale>`. Full guide: `../homestead-site-i18n`.

## Capability map (the whole surface at a glance)

- **Public API** (no token): `site` · `design` · `blocks` · `patterns` · `i18n/<loc>` · `media/<file>` ·
  `blogs[/slug]` · `pages[/slug]` · `health` · `openapi.json` · `auth/google` · `newsletter/subscribe` · `contact`.
- **Admin API** (`/admin/*`, token): `design` (+`/generate`,`/analyze-competitors`) · `blogs` (+`/generate`) ·
  `pages` · `compose/<target>/blocks` (+`/move`,`/duplicate`,`/batch`, `surfaces`) · `patterns` · `i18n/<loc>` · `media`.
- **Themes** — 18 one-shot presets (`POST /admin/design/generate {preset|industry}`): base `minimal` `bold-dark`
  `editorial` `corporate`; industry `tech` `healthcare` `restaurant` `realestate` `fitness` `beauty` `legal`
  `creative`; style `luxe` `education` `nonprofit` `finance` `playful` `neon`.
- **Blocks (15)** — `hero` `stats` `logos` `features` `problem` `comparison` `testimonials` `pricing` `faq`
  `cta` `section`(flexible) `steps` `gallery` `team` `banner`.
- **Fonts (all tokens)** — Inter(`--font-sans`) · Space Grotesk(`--font-grotesk`) · Spectral(`--font-display`) ·
  Fraunces(`--font-fraunces`) · Oswald(`--font-condensed`) · system mono.
- **Full categorized reference:** the live `/reference` page, or `docs/REFERENCE.zh.md` in the repo.

## Skill map

- **Content:** `homestead-site-blog` · `…-pages` · `…-newsletter`.
- **Design:** `homestead-site-design` (theme/tokens + the 18 templates) · `…-compose` (block-level page editing) ·
  `…-capture` (rebuild a section from a screenshot — flexible `section` block + `/patterns` library).
- **Media:** `homestead-site-media` (upload a photo → host it → drop into a gallery/team/hero/blog; upload-only).
- **Language:** `homestead-site-i18n` (translate content + chrome, path-based `/zh`). **Ops:** `homestead-site-ops` (deploy/status).
- **Entry:** `website` (the `/website` categorized command menu that routes to all of the above).

## Site basics & login (public, no token)

```bash
curl -s "$HOMESTEAD_SITE_API/health"        # {"database":"ok","status":"ok"} — readiness
curl -s "$HOMESTEAD_SITE_API/site"          # name, industry, audience, region, url
curl -s "$HOMESTEAD_SITE_API/openapi.json"  # full machine-readable contract

# Exchange a Google ID token (browser sign-in) for the site JWT:
curl -s -X POST "$HOMESTEAD_SITE_API/auth/google" -H "Content-Type: application/json" \
  -d '{"credential": "<google-id-token>"}'   # -> {"item":{"user":{...},"token":"<jwt>"}}
```
