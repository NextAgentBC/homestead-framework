# API Contract

The backend is intentionally OpenClaw-friendly: resources are grouped by domain, responses are JSON, and the surface stays small and stable.

**Authoritative sources:** the machine-readable contract is `GET /api/openapi.json`; a categorized human map (APIs · fonts · 18 themes · 15 blocks · skill↔API) is in [`REFERENCE.zh.md`](REFERENCE.zh.md). This page summarizes shape + conventions.

## Public Endpoints (no token)

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/site` | Public site config (name, locales, …) |
| `GET` | `/api/design` | Active design profile — tokens + sections (`?locale=`) |
| `GET` | `/api/blocks` | Block catalog: types, variants, fields, icons |
| `GET` | `/api/patterns` · `/api/patterns/:slug` | Saved section patterns (capture library) |
| `GET` | `/api/i18n/:locale` | UI chrome strings (nav/footer/buttons) |
| `GET` | `/api/media/:filename` | Self-hosted image |
| `GET` | `/api/openapi.json` | Machine-readable contract |
| `GET` | `/api/blogs` · `/api/blogs/:slug` | Published blog posts (`?locale=`) |
| `GET` | `/api/pages` · `/api/pages/:slug` | Published content pages (`?locale=`) |
| `POST` | `/api/auth/google` | Verify Google ID token, create/login user |
| `POST` | `/api/newsletter/subscribe` | Subscribe an email |
| `POST` | `/api/contact` | Send a contact message (also pings the operator on Telegram) |
| `POST` | `/api/chat` | Live chat — visitor message (`{sessionId?, message, locale?}`) answered by the sandboxed 小爪 brain; returns `{sessionId, reply}` (rate-limited) |
| `GET` | `/api/chat/:sessionId` | Live chat — full transcript for a session |

## Admin Endpoints

`Authorization: Bearer <token>` — from `/api/auth/google` (browser) or, for agents/CI, `flask --app app.main token issue --email <admin>` (non-interactive).

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/admin/blogs/generate` | Generate a draft/published AI blog |
| `POST` `PATCH` | `/api/admin/blogs` · `…/:id` | Create / update a blog post (`?locale=` localizes) |
| `POST` `PATCH` `DELETE` | `/api/admin/pages` · `…/:id` | Create / update / delete a content page |
| `GET` `PATCH` | `/api/admin/design` | Read / update tokens, sections, voice |
| `POST` | `/api/admin/design/generate` | Apply a preset/industry, or generate from competitors |
| `POST` | `/api/admin/design/analyze-competitors` | Fetch competitor signals → update design |
| `GET` | `/api/admin/surfaces` | List every editable surface (home + pages) + locales |
| `GET` | `/api/admin/consistency` | Audit coherence across every surface×locale (structural drift · missing/untranslated copy · wrong-language text · industry residue) → `{ok, findings[], summary}` |
| `GET` `POST` | `/api/admin/compose/:target/blocks` | List / add a block (or insert a `{pattern}`) |
| `PATCH` `DELETE` | `/api/admin/compose/:target/blocks/:id` | Update / remove a block |
| `POST` | `/api/admin/compose/:target/blocks/:id/move` · `…/duplicate` | Reorder / duplicate |
| `POST` | `/api/admin/compose/:target/batch` | Many block ops in one atomic call |
| `GET` | `/api/admin/revisions` | Edit history — snapshots newest-first; `?target=home\|:slug\|design` (+ `?locale=`) |
| `POST` | `/api/admin/undo` | Undo the last change to a surface (`{target, locale?}`); consumes its latest snapshot |
| `POST` | `/api/admin/revisions/:id/restore` | Restore a surface to a kept snapshot (current state snapshotted first) |
| `POST` `DELETE` | `/api/admin/patterns` · `…/:id` | Save / delete a reusable section pattern |
| `PATCH` | `/api/admin/i18n/:locale` | Edit UI chrome strings for a locale |
| `GET` `POST` | `/api/admin/media` | List / upload an image (upload-only, no generation) |
| `DELETE` | `/api/admin/media/:filename` | Delete a hosted image |
| `GET` | `/api/admin/chat` · `…/:sessionId` | List live-chat conversations / read one transcript |
| `POST` | `/api/admin/chat/:sessionId/reply` · `…/close` | Take over a chat (reply) / close-reopen it |

## Page composition (blocks)

A page (and the home page) is an ordered list of **blocks** — `{ id, type, variant, content }`. `GET /api/blocks` is the source of truth for the 15 types and their fields; edit a surface's block list through `/api/admin/compose/:target/*` (`target` = `home` or a page slug). Theme (colors/fonts) is separate — it lives in the design profile tokens, so structure and skin stay decoupled. Edits are instant (no redeploy). Full guide: `REFERENCE.zh.md` + the `oracle-site-compose` / `oracle-site-capture` skills.

## Design Profile

The frontend must not hard-code industry styling. It reads `GET /api/design` and maps tokens to CSS variables; `sections` (the block composition) drives the home page.

```json
{
  "item": {
    "name": "Professional Ledger",
    "source": "generated-from-industry-and-competitors",
    "industry": "accounting",
    "personality": "precise, steady, discreet, professional",
    "competitorUrls": ["https://example-accounting-firm.com"],
    "tokens": {
      "colors": {
        "ink": "#15201d",
        "muted": "#65706d",
        "paper": "#f6f7f4",
        "surface": "#ffffff",
        "line": "#d9dfda",
        "primary": "#1f5f4a",
        "accent": "#8f3f3b",
        "highlight": "#b88a2d",
        "link": "#275f91",
        "surfaceInverse": "#15201d",
        "inkInverse": "#f6f7f4",
        "onPrimary": "#ffffff"
      },
      "typography": {
        "body": "var(--font-sans), system-ui, -apple-system, sans-serif",
        "heading": "var(--font-grotesk), var(--font-sans), system-ui, sans-serif"
      },
      "radius": { "card": "8px", "control": "8px", "pill": "999px" },
      "layout": {
        "contentMaxWidth": "1120px",
        "heroMinHeight": "50vh",
        "density": "compact",
        "cardPadding": "20px",
        "sectionGap": "54px"
      }
    },
    "voice": {
      "headlineStyle": "plain offer or brand name",
      "tone": "precise, plainspoken, risk-aware"
    },
    "sections": [ { "type": "hero", "variant": "centered", "content": { } } ],
    "notes": "Design rationale and competitor observations."
  }
}
```

The three inverse keys (`surfaceInverse` / `inkInverse` / `onPrimary`) drive the dark "contrast band" (full-bleed hero + CTA banner) so even dark surfaces are token-driven, never hard-coded. Fonts are token stacks (`var(--font-*)`) wired in the frontend root layout: Inter, Space Grotesk, Spectral, Fraunces, Oswald.

## Competitor Analyzer

`POST /api/admin/design/analyze-competitors` accepts competitor URLs and optional OpenClaw visual observations. The backend fetches public HTML/CSS signals such as title, metadata, colors, font-family declarations, and basic content cues, then updates the active design profile.

Request:

```json
{
  "industry": "retail",
  "competitorUrls": [
    "https://example-retailer.com",
    "https://another-local-shop.com"
  ],
  "observations": [
    {
      "url": "https://example-retailer.com",
      "colors": ["#a6422b", "#28666e"],
      "fonts": ["Nunito Sans"],
      "layoutNotes": "Dense product grid, clear sale calls to action, warm editorial imagery."
    }
  ],
  "notes": "Use category conventions without copying brand identity."
}
```

## Response Shape

Successful object → `{ "item": { … } }`. Successful list → `{ "items": [ … ] }`. Write endpoints that return the changed block also include the surrounding `page`.

Error:

```json
{
  "error": {
    "code": "bad_request",
    "message": "Human readable message"
  }
}
```

Common codes: `401` missing/bad token, `403` not admin, `404` not found, `400` bad input, `413` upload too large.
