---
name: oracle-site-block-logos
description: "Logo / trust strip block — add or edit a logo / trust strip on any Oracle Site page by natural language. Thin recipe over the compose engine (logos). Triggers (zh+en): 加 logo 墙 / 合作伙伴 / 技术栈条 / add a logo or trust strip."
metadata:
  version: 0.1.0
  generated: true
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Logo / trust strip block (`logos`)

> Auto-generated from the block manifest (`GET /api/blocks`). Full engine, rules,
> and edit/move/remove recipes: `../oracle-site-compose/SKILL.md`.
> Prerequisite: `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.

A heading plus a row of text chips (partners, tech, press).

- Variants: `default`
- Content fields: `heading` (text), `items` (list)

`target` is `home` or a page slug. Adding scaffolds sensible defaults, so the
block looks complete immediately — pass `content` only to override.

```bash
# Add a logo / trust strip to the home page
curl -s -X POST "$ORACLE_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"logos","position":"end"}'
```

To **edit / move / remove** an existing one: list blocks to get its id, then use
the compose engine (PATCH content, `/move`, DELETE) or a `batch` call. For
multi-step requests prefer `POST /admin/compose/{target}/batch`. See
`../oracle-site-compose/SKILL.md`.
