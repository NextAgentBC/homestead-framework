# Design System & Section Composition — Design Spec

> **Status: ✅ shipped — and extended well beyond this spec.** This is the original design
> proposal, kept as an architecture/decision record. The live system now has **18 style presets**
> (not 3–4), **15 block types** (not 5), path-based i18n (`/zh`), and image upload. Authoritative
> current state: [`REFERENCE.zh.md`](REFERENCE.zh.md) + the `homestead-site-design` / `homestead-site-compose`
> skills. Principles below still hold: subtract, reuse, modular, maintainable, no duplicate systems.

## 1. Goal / Non-goal

**Goal:** let a user (via the OpenClaw Telegram skill) say *"make it like Apple"* / *"like Tesla"* / *"clean and minimal for an accounting firm"* and get a **real landing page** — hero, what-we-do, CTA, blog, footer — in a chosen **style**, with **2–3 options** to pick from, then fine-tune.

**Non-goal:** a pixel-perfect clone of apple.ca/tesla.com, or a general drag-and-drop page builder. We ship a **curated set** of section variants + style presets ("Apple-*inspired*"), not infinite layouts and not copied brand assets.

## 2. What already exists (reuse — do not duplicate)

| Piece | Reuse for |
|---|---|
| `DesignProfile` + `tokens` (colors/type/radius/layout) → CSS vars in `globals.css` | the **theme/skin** layer (unchanged) |
| `design_service.py` `INDUSTRY_PRESETS`, `profile_for_industry`, `deep_merge` | extend into style presets |
| `/admin/design` (GET/PATCH), `/admin/design/generate`, `/admin/design/analyze-competitors` | apply themes; read a reference site (e.g. apple.ca) for palette cues |
| `homestead-site-design` skill | upgrade into the conversational designer |
| `app/page.tsx` hardcoded sections (hero / Operating Model / Latest Blogs) | becomes the first data-driven composition |
| `Page` content type (just built) | unrelated — pages are markdown prose; sections are structured. Keep separate. |

**The only missing layer is structure** — sections are hardcoded in `page.tsx`. That's what this spec adds.

## 3. Architecture: two layers

1. **Theme (skin)** = `tokens` (palette, fonts, radius, spacing) + `mode: light|dark` + heading scale. → already `DesignProfile.tokens`.
2. **Composition (structure)** = an ordered list of **sections**, each `{ type, variant, content }`. → **new**, stored alongside the theme.

A single `<SectionRenderer>` maps `type + variant` → a component variant; the home page renders the composition instead of hardcoded JSX. Every section reads theme via CSS vars (already themed), so theme and structure stay decoupled.

## 4. Section catalog (Phase 1)

> ✅ Shipped & grown to **15 block types** (hero, stats, logos, features, problem, comparison,
> testimonials, pricing, faq, cta, section, steps, gallery, team, banner). `GET /api/blocks` is the
> source of truth; the flexible `section` block + pattern library cover novel layouts with no code.
> The table below is the original Phase-1 seed.
>
> ✅ Also shipped: `hero`/`cta` take a photo (`image` + `imageFocal`/`imageAlt`; full-bleed
> background or split side-image) behind a token-driven scrim; **empty image slots render a
> prompt-labelled placeholder** (`imagePrompt`) so a site needs no image generator. Industry
> presets (beauty/restaurant/healthcare/legal/fitness) are complete, image-ready templates.
> Site-level ops: `POST /admin/site/rebrand` (atomic industry switch → declared imagery +
> audit) · `GET /admin/consistency` (coherence audit = the "definition of done").

| type | variants | content fields |
|---|---|---|
| `hero` | `split` (current) · `centered` (Apple-style, big type + whitespace) · `fullbleed` (Tesla-style, full-width image/overlay, bold) | `kicker, headline, subhead, cta{label,href}, secondaryCta?, image?, imageFocal?, imageAlt?, imagePrompt?` |
| `features` ("what we do") | `cards` (current) · `rows` (alternating text/visual) · `minimal` (icon columns) | `heading, items[]{icon,title,body}` |
| `cta` | `banner` (full-width) · `boxed` | `headline, subhead?, cta{label,href}` |
| `blog` | `grid` (current) | `heading, limit` |
| `footer` | `minimal` (current) · `columns` | `tagline, links[]{label,href}` |

`header`/nav already exists (`SiteNav`) and auto-lists Pages — keep, optionally add a `transparent-on-hero` variant later.

## 5. Composition data model

Extend the **active design config** with a `sections` array (single source of truth: the design profile fully describes the landing page's look **and** structure):

```jsonc
{
  "tokens": { "colors": {…}, "typography": {…}, "radius": {…}, "layout": {…}, "mode": "light" },
  "sections": [
    { "type": "hero", "variant": "centered",
      "content": { "kicker": "Accounting", "headline": "Books you can trust",
                   "subhead": "…", "cta": { "label": "Book a call", "href": "/contact" } } },
    { "type": "features", "variant": "minimal",
      "content": { "heading": "What we do",
                   "items": [ { "icon": "calculator", "title": "Tax", "body": "…" }, … ] } },
    { "type": "cta", "variant": "banner",
      "content": { "headline": "Ready to tidy your books?", "cta": { "label": "Start", "href": "/contact" } } },
    { "type": "blog", "variant": "grid", "content": { "heading": "Insights", "limit": 3 } }
  ]
}
```

- If `sections` is absent, the frontend renders a **safe default composition** (today's layout) — backward compatible.
- Content (headlines, items) lives in the section `content`; sensible defaults derive from `site` config + `voice` so a fresh profile already looks complete.

> Open decision (§12): keep composition inside `DesignProfile`, or a separate `SiteLayout` model. Recommendation: inside `DesignProfile` for now (one object, one API) — revisit if multi-page layouts arrive.

## 6. Style presets (the "options")

Each preset = `{ tokens (incl. mode) + sections (types/variants) + default content tone }`, named and tagged by vibe/industry. Extends `INDUSTRY_PRESETS`.

> ✅ Shipped & grown to **18 presets**: base (`minimal`, `bold-dark`, `editorial`, `corporate`) + industry (`tech`, `healthcare`, `restaurant`, `realestate`, `fitness`, `beauty`, `legal`, `creative`) + style (`luxe`, `education`, `nonprofit`, `finance`, `playful`, `neon`). `POST /admin/design/generate {preset|industry}`. The table below is the original seed of 3.

| Preset | Vibe | Hero | Palette/mode | Features |
|---|---|---|---|---|
| `minimal` | Apple-*inspired* | `centered`, huge type, max whitespace | neutral + 1 accent, light, large heading scale | `minimal` |
| `bold-dark` | Tesla-*inspired* | `fullbleed`, image/overlay | dark, high-contrast | `rows` |
| `editorial` | current default | `split` | warm light | `cards` |
| `professional` / `warm-retail` / … | industry presets | per industry | per industry | per industry |

"Make it like apple.ca" → agent offers `minimal` (+ optionally feeds `apple.ca` to `analyze-competitors` for palette cues, reusing existing). Picking a preset PATCHes `tokens + sections` onto the active profile.

## 7. Frontend rendering

- `components/sections/` — one component per `type`, each handling its `variant`s via the themed CSS-var classes (extend `globals.css`, no hardcoded colors).
- `components/section-renderer.tsx` — `sections.map(s => render[s.type](s))`; unknown types ignored.
- `app/page.tsx` — fetch active design (`getDesign()`), render `<SectionRenderer sections={design.sections ?? DEFAULT_SECTIONS} />`.
- Reuse: `react-markdown` for any rich text, `lucide-react` icons (already deps), existing `.hero/.section/.grid/.post-card/.button` classes as variant building blocks.

## 8. Backend / API changes

- `DesignProfile`: add `sections` (JSON, default `[]`) + migration. Add `mode` to tokens (default `light`).
- `/design` (public) and `/admin/design` (GET): return `sections`.
- `/admin/design` (PATCH): already deep-merges arbitrary keys → accepts `sections` (replace, not merge, since it's an ordered list).
- `design_service.py`: add `STYLE_PRESETS` (the table in §6) and `apply_preset(name)` → returns tokens+sections.
- `/admin/design/generate`: accept optional `preset` / `style` (and keep `industry` + `competitorUrls`). No new endpoint needed.

## 9. OpenClaw design skill (conversational — the "更牛" part)

Upgrade `homestead-site-design` from "pass an industry" to a guided runbook:

1. **Interview** (ask, don't assume): industry? a reference site or vibe (minimal / bold / warm / professional)? light or dark?
2. **Offer 2–3 options**: preset name + hero style + palette + one-line rationale. (Optionally run `analyze-competitors` on a named reference for palette cues.)
3. **Apply** the chosen one → `PATCH /admin/design` with `{tokens, sections}` (or `generate` with `preset`).
4. **Fine-tune on request**: "hero → fullbleed", "primary darker", "CTA text = …", "drop testimonials" → targeted PATCH.

All through existing design endpoints. Triggers (zh+en) added to the skill description.

## 10. Honest boundaries

- Curated **inspired-by** styles, not brand clones (legal + scope). `analyze-competitors` already states "never copy exact brand identity".
- A bounded variant set (a few per section), not arbitrary layouts.
- Real images/video for `fullbleed` heroes are the user's asset to provide (Phase 2 adds upload); Phase 1 uses color/gradient + provided URL.

## 11. Phasing

- **Phase 0 (prerequisite):** fix the frontend build failure; land the nav `no-store` fix so new pages hit the menu immediately. *(Required before any of this — it all needs a working build.)*
- **Phase 1 (this spec):** Section catalog §4, composition model §5, 3–4 presets §6, `SectionRenderer`, data-driven home, upgraded skill §9.
- **Phase 2 — ✅ shipped:** testimonials/logos + 10 more block types, per-page compositions, **image upload** (`/api/admin/media`, upload-only), path-based i18n (`/zh`), screenshot capture + pattern library. (`transparent-on-hero` header not pursued.)

## 12. Decisions (locked)

1. **Composition storage:** inside `DesignProfile.sections` (one object, one API).
2. **Dark mode:** yes in Phase 1 — add `tokens.mode = light|dark` (required by `bold-dark`).
3. **Phase 1 presets:** `minimal` (Apple-inspired) · `bold-dark` (Tesla-inspired) · `editorial` (default), plus the existing `education`/`accounting`/`retail` palettes as industry options.
4. **Reference library:** seed `backend/app/data/style_references.json` from ~6 design exemplars (apple, tesla, stripe, linear, airbnb, notion) → `{palette hints, vibe, mapped family}`; the skill can also analyze a user-named site live via `analyze-competitors`. Inspired-by signals only — never brand clones.
5. **Content authoring:** via skill/API only for now; a small admin form is Phase 2.

## 13. Phase 0 — DONE ✅

Frontend build fixed (root layout `force-dynamic`, no build-time prerender hang); nav is `no-store` so a newly published Page appears in the menu immediately (verified: creating an About + Services page showed both in the nav instantly). Pages mechanism + 6 OpenClaw skills shipped earlier. Phase 1 (sections/composition + presets + reference library + upgraded design skill) is next.
