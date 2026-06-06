---
name: homestead-site-block-testimonials
description: "Testimonials block — add or edit a testimonials on any Homestead page by natural language. Thin recipe over the compose engine (testimonials). Triggers (zh+en): 加评价 / 用户证言 / 口碑 / add testimonials / quotes."
metadata:
  version: 0.1.0
  generated: true
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Testimonials block (`testimonials`)

> Auto-generated from the block manifest (`GET /api/blocks`). Full engine, rules,
> and edit/move/remove recipes: `../homestead-site-compose/SKILL.md`.
> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.

Quote cards with author and role.

- Variants: `default`
- Content fields: `heading` (text), `items` (list)

`target` is `home` or a page slug. Adding scaffolds sensible defaults, so the
block looks complete immediately — pass `content` only to override.

```bash
# Add a testimonials to the home page
curl -s -X POST "$HOMESTEAD_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"testimonials","position":"end"}'
```

To **edit / move / remove** an existing one: list blocks to get its id, then use
the compose engine (PATCH content, `/move`, DELETE) or a `batch` call. For
multi-step requests prefer `POST /admin/compose/{target}/batch`. See
`../homestead-site-compose/SKILL.md`.
