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

## Auth (admin token)

Admin routes require `Authorization: Bearer <jwt>`. Two ways to get one:

1. **Interactive (browser):** Google Sign-In on the site (`POST /auth/google`).
2. **Non-interactive (agents — no browser):** run where the backend runs:

```bash
export HOMESTEAD_SITE_TOKEN="$(docker compose -f /home/ubuntu/projects/homestead-site/docker-compose.yml \
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
