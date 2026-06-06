---
name: homestead-site-capture
description: "Rebuild a section from a screenshot the user liked and add it to an Homestead page — harmonized to the current theme (never a pixel copy). Maps the shot to an existing block when possible, else to the flexible `section` block (a token-driven layout DSL). Optionally saves it to the pattern library so it's reusable. Triggers (zh+en): '看到一个网站的板块/这个 section 不错/照着这个截图做一个', 'clone this section / build this from the screenshot / recreate this layout', '把这个截图变成一个板块', '加到模板里/存成可复用的板块/save as a pattern', 'make it match my site / 同化成我的风格'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
        - jq
---

# Homestead — Capture (screenshot → section)

> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.
> Structure edits go through the compose engine — see `../homestead-site-compose/SKILL.md`.

The user sends a screenshot of a section they like. **You** (the agent) look at it,
infer its *structure* — not its colors — and rebuild it from blocks. Colors, fonts,
radius and spacing all come from the site's design tokens, so the result automatically
matches the current theme. This is **assimilation, not cloning.**

## The golden rule
**Inspiration only — never copy a brand's exact colors, logos, photos, or copy.**
Borrow layout, density, hierarchy, and content *intent*. Rebuild with the site's tokens.

## Workflow

**1. Read the theme + the catalog (so you compose with real values):**
```bash
curl -s "$HOMESTEAD_SITE_API/design"  | jq '.item.tokens'            # the palette you must harmonize to
curl -s "$HOMESTEAD_SITE_API/blocks"  | jq '.items[] | {type, variants, fields:[.fields[].key]}'
```

**2. Decide how to rebuild it:**
- **Maps to an existing block?** (a hero, features grid, pricing, testimonials, FAQ, stats, comparison…) → use that block. Best fidelity + semantics. See the compose skill.
- **Novel layout the fixed blocks don't cover?** → use the flexible **`section`** block (below).

**3. Insert it** (instant, no redeploy). For a multi-part capture, prefer one `batch` call.

**4. (Optional) Save it as a pattern** so it's reusable on any page/site (§ Pattern library).

## The flexible `section` block

One token-driven block that expresses most "section" layouts. Shape:
```jsonc
{ "type": "section", "variant": "grid",   // grid | split | stack | banner
  "content": {
    "eyebrow": "", "heading": "", "subhead": "",
    "layout": { "columns": 3, "align": "center", "media": "none", "tone": "plain" },
    //  columns 1-4 · align left|center · media none|left|right|top · tone plain|tint|inverse
    "items": [ { "kind": "feature", "icon": "zap", "title": "...", "body": "..." } ]
    //  kind: feature | stat | quote | step | media | text | button
    //  feature{icon,title,body} stat{value,label} quote{quote,author,role}
    //  step{title,body} media{image,title} text{title,body} button{title,href}
    , "cta": { "label": "", "href": "" }
  } }
```
`tone:"inverse"` renders the section on the dark contrast-band tokens — use it when the
screenshot's section is dark, and it still matches the brand. `icon` ∈ sparkles, mail,
shield, gauge, layers, zap, book, cloud.

Add one (harmonized — note there are **no colors** in the payload):
```bash
curl -s -X POST "$HOMESTEAD_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"section","variant":"grid","content":{
        "heading":"How it works","layout":{"columns":3,"align":"center","tone":"tint"},
        "items":[
          {"kind":"step","title":"Sign up","body":"Create your account in a minute."},
          {"kind":"step","title":"Connect","body":"Link your tools in a click."},
          {"kind":"step","title":"Launch","body":"Go live the same day."}]}}'
```

## Pattern library (make it reusable — the library grows)

```bash
# Save the block you just added (capture it straight off the page by id):
curl -s -X POST "$HOMESTEAD_SITE_API/admin/patterns" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"How it works (3 steps)","target":"home","blockId":"b_xxxx","tags":["steps","onboarding"]}'
#   …or save an explicit spec: {"name":"…","spec":{"type":"section","content":{…}}}

curl -s "$HOMESTEAD_SITE_API/patterns" | jq '.items[] | {slug,name,type}'   # browse the library (public)

# Re-use a saved pattern on any page — it's scaffolded fresh and re-harmonized:
curl -s -X POST "$HOMESTEAD_SITE_API/admin/compose/about/blocks" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"pattern":"how-it-works-3-steps","position":"end"}'
```

## Adopt some of the screenshot's palette (optional)
If the user also loves the *colors*, feed your visual read to the analyzer instead of
hardcoding hex — it produces a distinct, harmonized palette (see `../homestead-site-design`):
```bash
curl -s -X POST "$HOMESTEAD_SITE_API/admin/design/analyze-competitors" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"industry":"...","competitorUrls":["https://the-source.example"],"observations":[{"url":"https://the-source.example","colors":["#0f172a","#22d3ee"],"fonts":["Inter"],"layoutNotes":"dark bento grid"}],"notes":"Inspiration only — create a distinct identity."}'
```

## Bilingual capture
If the site has a `zh` locale, add the section in both languages in one go: insert once
(default locale), then repeat the `add` with `?locale=zh` and translated `content`. See
`../homestead-site-i18n/SKILL.md`.

## Capture vs. upload (route the user's image correctly)
This skill is for **replicating a layout** you *see* in a screenshot — rebuilt in the site's
tokens, never hosting the shot. If instead the user wants to **display a real photo as-is**
(a headshot, product/food shot, a blog image), that's an **upload**, not a capture — host it
via `../homestead-site-media/SKILL.md` and put the returned `/api/media/<file>` URL into a
gallery / team / testimonial / `section` `media` item or a `body_markdown` image.

## Rules
- Harmonize, don't clone. No raw colors in `section` payloads — tokens do that.
- A real *photo to show* is an upload (`../homestead-site-media/SKILL.md`), not a capture.
- Prefer a real semantic block over `section` when the shot clearly *is* one (pricing, FAQ…).
- Discover before you write (`/blocks`, the target's block list). Read `error.message` and retry.
- A brand-new *coded* block type is still a code change; `section` + patterns cover the no-redeploy path.
