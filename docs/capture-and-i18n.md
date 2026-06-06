# Capture & i18n — architecture

Two capabilities, one thesis: **the OpenClaw agent is the intelligence; the
backend stays a safe, schema-validated, token-driven, no-redeploy data store.**

- **Capture** — the agent looks at a screenshot of a section it likes and rebuilds
  it from a flexible, token-driven block (auto-harmonized to the current theme).
  Good captures are saved as reusable **patterns**, so the library grows without
  code changes.
- **i18n** — content is never hard-coded in one language. Every localizable entity
  carries an `i18n` map; the **agent does the translation** (it reads the English
  blocks and writes the Chinese ones). Routing is path-based (`/zh/...`) for SEO.

---

## 1. Capture — flexible `section` block + pattern library

### The flexible block (`section`)
A single new block type whose `content` is a small **layout DSL**, rendered once
by a token-only React component (`frontend/components/sections.tsx`). Because it
reads *only* design tokens (colors / fonts / radius / spacing from `/api/design`),
any captured section automatically adopts the site's look — assimilation by
construction. The screenshot informs **structure, density, hierarchy, content**,
never raw colors.

```jsonc
{
  "type": "section",
  "variant": "grid",              // grid | split | stack | banner
  "content": {
    "eyebrow": "", "heading": "", "subhead": "",
    "layout": { "columns": 3, "align": "center", "media": "none", "tone": "plain" },
    //  columns 1–4 · align left|center · media none|left|right|top · tone plain|tint|inverse
    "items": [
      { "kind": "feature", "icon": "zap", "title": "...", "body": "..." },
      { "kind": "stat", "value": "99%", "label": "..." },
      { "kind": "quote", "quote": "...", "author": "...", "role": "..." },
      { "kind": "step", "title": "...", "body": "..." },
      { "kind": "media", "image": "https://…", "title": "..." },
      { "kind": "text", "title": "...", "body": "..." },
      { "kind": "button", "label": "...", "href": "/contact" }
    ],
    "cta": { "label": "", "href": "" }
  }
}
```
`tone: "inverse"` paints the section on the inverse-surface tokens (`surfaceInverse`
/ `inkInverse`) added in the design-token pass — so a captured *dark* band still
matches the brand.

### Pattern library (`BlockPattern`)
A DB table of named, reusable section specs. The agent saves a good capture once;
it becomes insertable everywhere, like the coded blocks.

- `GET  /api/patterns` · `GET /api/patterns/<slug>` — public catalog
- `POST /api/admin/patterns` — save a block (or raw spec) as a pattern
- `DELETE /api/admin/patterns/<id>`
- compose `add` accepts `{ "pattern": "<slug>" }` to scaffold from a saved pattern.

**Graduation path (optional, later):** a popular pattern can be promoted to a
hand-coded block type (manifest + renderer) via a normal PR. Not required for the
agent loop.

### The skill — `homestead-site-capture`
1. View the screenshot. 2. `GET /api/design` (tokens) + `GET /api/blocks` (catalog).
3. If it maps cleanly to an existing block → compose that, harmonized. Else → emit
a `section` DSL block. 4. Insert via compose (optionally `batch` to also fill the
zh locale). 5. Optionally `POST /admin/patterns` to save it. **Rule: inspiration
only — rebuild with our tokens, never copy the source's exact colors/assets.**
Optional `adopt-palette` mode feeds observed colors to `analyze-competitors`.

---

## 2. i18n — path-based `/zh`, agent as translator

### Storage — one `i18n` JSON column per localizable model
`{ "<locale>": { "<field>": <value>, … } }`. Base columns hold the default locale;
`i18n[locale]` overrides per field. Resolution is locale-agnostic:
`value = (i18n or {}).get(locale, {}).get(field, base_field)`.

| Model | base (default locale) | `i18n[locale]` may override |
|---|---|---|
| `DesignProfile` (home) | `sections` | `sections` |
| `Page` | `title`, `body_markdown`, `sections`, `nav_label`, `meta_*` | same keys |
| `BlogPost` | `title`, `excerpt`, `body_markdown`, `tags`, `meta_*` | same keys |
| `UiMessages` (new) | — | `messages` (chrome strings) per locale row |

Slugs are shared across locales; the `/zh` URL prefix makes each page a distinct,
indexable URL without duplicate rows.

### Config
`SITE_LOCALES` (csv, default `en`) and `SITE_DEFAULT_LOCALE` (default `en`),
surfaced in `GET /api/site` as `locales` + `defaultLocale`.

### API (locale-aware)
- `GET /api/site` → `locales`, `defaultLocale`.
- `GET /api/design?locale=zh`, `GET /api/blogs?locale=zh`, `GET /api/blogs/<slug>?locale=zh`,
  `GET /api/pages?locale=zh`, `GET /api/pages/<slug>?locale=zh` → localized payloads (fallback to default).
- `GET /api/i18n/<locale>` → UI chrome strings (public). `PATCH /api/admin/i18n/<locale>` → edit them.
- Admin writes are locale-aware via `?locale=`: compose / pages / blogs edit `i18n[locale]`
  when `locale` ≠ default, base columns otherwise.

### Frontend (path-based)
- `frontend/middleware.ts` — prefixes any un-prefixed path with a locale (cookie →
  `Accept-Language` → default) and validates the locale segment.
- Routes move under `app/[locale]/…`; `app/[locale]/layout.tsx` sets `<html lang>`,
  `data-mode`/`data-theme`, nav/footer, and a **language toggle**.
- `lib/i18n.ts` — `getMessages(locale)` + `t(key)` with an English fallback dict;
  `lib/api.ts` fetchers take `locale`.
- SEO: `hreflang` alternates in metadata; `sitemap.ts` lists every locale; canonical
  per locale.

### The skill — `homestead-site-i18n`
The agent *is* the translator. Verbs: "translate the home/a page/a post to zh"
(read default-locale content → write `i18n.zh`), "fix the Chinese nav/footer" (PATCH
UI messages), "add a Chinese blog post". compose/pages/blog skills gain a `locale`
note so any edit can target a locale.

---

## Build order
config+models+migration → locale-aware API + patterns API → capture renderer/CSS →
`[locale]` routing + middleware + i18n lib + nav/sitemap → skills → verify
(migration upgrade, pytest, typecheck, build).
