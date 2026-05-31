---
name: oracle-site-block-comparison
description: "Comparison (us vs. them) block — add or edit a comparison (us vs. them) on any Oracle Site page by natural language. Thin recipe over the compose engine (comparison). Triggers (zh+en): 加对比 / 我们 vs 别人 / before after / add a comparison table."
metadata:
  version: 0.1.0
  generated: true
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Comparison (us vs. them) block (`comparison`)

> Auto-generated from the block manifest (`GET /api/blocks`). Full engine, rules,
> and edit/move/remove recipes: `../oracle-site-compose/SKILL.md`.
> Prerequisite: `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.

Two columns; the right one is highlighted as the better choice.

- Variants: `default`
- Content fields: `heading` (text), `left` (column), `right` (column)

`target` is `home` or a page slug. Adding scaffolds sensible defaults, so the
block looks complete immediately — pass `content` only to override.

```bash
# Add a comparison (us vs. them) to the home page
curl -s -X POST "$ORACLE_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"comparison","position":"end"}'
```

To **edit / move / remove** an existing one: list blocks to get its id, then use
the compose engine (PATCH content, `/move`, DELETE) or a `batch` call. For
multi-step requests prefer `POST /admin/compose/{target}/batch`. See
`../oracle-site-compose/SKILL.md`.
