---
name: oracle-site-pages
description: "Create and manage standalone content pages (About, Services, Privacy, FAQ…) on the Oracle Site over its API — they render instantly with NO rebuild and auto-appear in the nav. Triggers: '做一个 About 页面 / 加个关于我们页', 'make an about us page', '新建页面 / 加一页', 'create a page', '改 about 页 / 更新页面', '删页面', 'services 页 / 隐私政策页'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Oracle Site — Pages (content pages)

> Prerequisite: `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.

Standalone pages (About, Services, Privacy, FAQ…) are **data, not code**: created via this API,
rendered by the frontend's `/{slug}` route **instantly, no rebuild**, and listed in the nav when published.

Use this for content/marketing pages. For bespoke interactive pages (complex layout/JS), edit the
frontend code instead — that's the dev loop, not this skill.

## Public (no auth)

```bash
curl -s "$ORACLE_SITE_API/pages"          # published pages (nav): slug, navLabel, navOrder, showInNav
curl -s "$ORACLE_SITE_API/pages/<slug>"   # one published page incl. bodyMarkdown
```

## Admin (Bearer token)

```bash
# Create + publish an About page → live at https://<site>/about immediately
curl -s -X POST "$ORACLE_SITE_API/admin/pages" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "title": "About Us",
    "slug": "about",
    "body_markdown": "We help small teams ship a real website fast.\n\n## What we do\n\n- ...",
    "status": "published",
    "nav_label": "About",
    "nav_order": 10,
    "show_in_nav": true,
    "meta_description": "About our company"
  }'

# Update a page (partial: publish a draft, edit body, reorder nav…)
curl -s -X PATCH "$ORACLE_SITE_API/admin/pages/<id>" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"status": "published", "nav_order": 20}'

# Delete a page
curl -s -X DELETE "$ORACLE_SITE_API/admin/pages/<id>" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN"
```

## Module-composed pages (landing pages)

A page can be built from **design modules** (hero, features, pricing, faq, cta…) — the same modules as the home — instead of markdown. Pass `sections` instead of `body_markdown`; see `../oracle-site-design/SKILL.md` for the module catalog and content shapes.

```bash
curl -s -X POST "$ORACLE_SITE_API/admin/pages" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "title": "Services", "slug": "services", "status": "published", "nav_label": "Services",
    "sections": [
      {"type":"hero","variant":"centered","content":{"badge":"What we offer","headline":"Services","headlineAccent":"that scale.","subhead":"...","cta":{"label":"Contact","href":"/contact"}}},
      {"type":"pricing","content":{"heading":"Plans","items":[{"name":"Basic","price":"$X","features":["..."],"cta":{"label":"Start","href":"/contact"}}]}},
      {"type":"faq","content":{"heading":"FAQ","items":[{"q":"...","a":"..."}]}}
    ]
  }'
```

## Page templates (recipes by page — one-shot scaffold)

Don't hand-write the section list — **scaffold a whole page from a recipe**. The block library is
organized *by page*; pass `{"template":"<name>"}` and the page is composed for you, then refine.

| template | builds | sections (in order) |
|---|---|---|
| `home` | landing | hero · stats · logos · features · steps · comparison · cta |
| `about` | About | hero · section(story) · stats · team · cta |
| `services` | Services | hero · features · steps · pricing · faq · cta |
| `solutions` | Solutions | hero · problem · features · steps · testimonials · cta |
| `pricing` | Pricing | hero · pricing · comparison · faq · cta |
| `landing` | Campaign landing | hero(fullbleed) · features · testimonials · pricing · cta |
| `restaurant` | Restaurant / café | hero · features · gallery · testimonials · banner · cta |
| `clinic` | Clinic / healthcare | hero · features · steps · team · faq · cta |
| `law` | Law firm / advisory | hero · features · stats · testimonials · faq · cta |

> Industry recipes pair well with the matching **theme** preset — e.g. scaffold `restaurant` + `generate {"preset":"restaurant"}` (see `../oracle-site-design`).

```bash
curl -s "$ORACLE_SITE_API/page-templates"          # browse the recipes (public)
# scaffold + publish a Services page, then tweak any block via the compose skill
curl -s -X POST "$ORACLE_SITE_API/admin/pages" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"template":"services","slug":"services","status":"published","nav_label":"Services"}'
```
`title` defaults to the recipe label (pass your own to override). After scaffolding, refine copy with
`../oracle-site-compose/SKILL.md` and translate with `?locale=zh`. **contact** + **blog** aren't here —
they're built-in frontend routes (the contact form and blog index aren't composed from blocks).

Notes:
- A page uses `sections` if present, otherwise `body_markdown`. Provide one of them (or a `template`).
- `body_markdown` is the content **below** the heading — the page renders `title` as the `<h1>` automatically, so don't repeat it as a leading `# Title` (avoids a duplicate heading).
- Create requires `title` + `body_markdown`. `slug` auto-derives from title if omitted; duplicates get `-2`, `-3`.
- Reserved slugs (`blog`, `contact`, `api`, `admin`, …) are rejected — taken by built-in routes.
- `status`: `draft` (hidden) or `published` (live + in nav). `nav_order` ascending; `show_in_nav:false` keeps a page reachable by URL but out of the nav.
- The page URL is live immediately; the nav list refreshes within ~5 min (cached).
