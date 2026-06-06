---
name: homestead-site-block-cta
description: "Call to action block — add or edit a call to action on any Homestead page by natural language. Thin recipe over the compose engine (cta). Triggers (zh+en): 加行动号召 / CTA / 引导按钮区 / add a CTA banner."
metadata:
  version: 0.1.0
  generated: true
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Call to action block (`cta`)

> Auto-generated from the block manifest (`GET /api/blocks`). Full engine, rules,
> and edit/move/remove recipes: `../homestead-site-compose/SKILL.md`.
> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.

A full-width banner with a headline and a button.

- Variants: `banner`
- Content fields: `headline` (text), `subhead` (textarea), `cta` (cta)

`target` is `home` or a page slug. Adding scaffolds sensible defaults, so the
block looks complete immediately — pass `content` only to override.

```bash
# Add a call to action to the home page
curl -s -X POST "$HOMESTEAD_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"cta","position":"end"}'
```

To **edit / move / remove** an existing one: list blocks to get its id, then use
the compose engine (PATCH content, `/move`, DELETE) or a `batch` call. For
multi-step requests prefer `POST /admin/compose/{target}/batch`. See
`../homestead-site-compose/SKILL.md`.
