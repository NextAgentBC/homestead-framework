---
name: homestead-site-block-banner
description: "Highlight banner block — add or edit a highlight banner on any Homestead page by natural language. Thin recipe over the compose engine (banner). Triggers (zh+en): 加横幅 / 公告条 / 提示条 / 促销条 / add a banner / announcement strip."
metadata:
  version: 0.1.0
  generated: true
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Highlight banner block (`banner`)

> Auto-generated from the block manifest (`GET /api/blocks`). Full engine, rules,
> and edit/move/remove recipes: `../homestead-site-compose/SKILL.md`.
> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.

A slim highlight strip — an icon, a short message, and an optional button. Good for announcements or offers.

- Variants: `default` · `tint`
- Content fields: `icon` (icon), `text` (text), `cta` (cta)
- Icons: sparkles, mail, shield, gauge, layers, zap, book, cloud

`target` is `home` or a page slug. Adding scaffolds sensible defaults, so the
block looks complete immediately — pass `content` only to override.

```bash
# Add a highlight banner to the home page
curl -s -X POST "$HOMESTEAD_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"banner","position":"end"}'
```

To **edit / move / remove** an existing one: list blocks to get its id, then use
the compose engine (PATCH content, `/move`, DELETE) or a `batch` call. For
multi-step requests prefer `POST /admin/compose/{target}/batch`. See
`../homestead-site-compose/SKILL.md`.
