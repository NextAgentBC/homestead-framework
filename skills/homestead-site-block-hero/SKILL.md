---
name: homestead-site-block-hero
description: "Hero block — add or edit a hero on any Homestead page by natural language. Thin recipe over the compose engine (hero). Triggers (zh+en): 加个 hero / 改首屏标题 / 改大标题 / add a hero / change the headline / hero 换居中或大图."
metadata:
  version: 0.1.0
  generated: true
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Hero block (`hero`)

> Auto-generated from the block manifest (`GET /api/blocks`). Full engine, rules,
> and edit/move/remove recipes: `../homestead-site-compose/SKILL.md`.
> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.

Top-of-page headline with optional badge/eyebrow, subhead, and up to two CTAs.

- Variants: `split` · `centered` · `fullbleed`
- Content fields: `badge` (text), `kicker` (text), `headline` (text), `headlineAccent` (text), `subhead` (textarea), `cta` (cta), `secondaryCta` (cta)

`target` is `home` or a page slug. Adding scaffolds sensible defaults, so the
block looks complete immediately — pass `content` only to override.

```bash
# Add a hero to the home page
curl -s -X POST "$HOMESTEAD_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"hero","position":"end"}'
```

To **edit / move / remove** an existing one: list blocks to get its id, then use
the compose engine (PATCH content, `/move`, DELETE) or a `batch` call. For
multi-step requests prefer `POST /admin/compose/{target}/batch`. See
`../homestead-site-compose/SKILL.md`.
