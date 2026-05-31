---
name: oracle-site-block-stats
description: "Stats / KPIs block — add or edit a stats / kpis on any Oracle Site page by natural language. Thin recipe over the compose engine (stats). Triggers (zh+en): 加一排数据 / KPI / 指标条 / add stats / metrics row / 改数字."
metadata:
  version: 0.1.0
  generated: true
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Stats / KPIs block (`stats`)

> Auto-generated from the block manifest (`GET /api/blocks`). Full engine, rules,
> and edit/move/remove recipes: `../oracle-site-compose/SKILL.md`.
> Prerequisite: `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.

A row of metric value + label pairs.

- Variants: `default`
- Content fields: `items` (list)

`target` is `home` or a page slug. Adding scaffolds sensible defaults, so the
block looks complete immediately — pass `content` only to override.

```bash
# Add a stats / kpis to the home page
curl -s -X POST "$ORACLE_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"stats","position":"end"}'
```

To **edit / move / remove** an existing one: list blocks to get its id, then use
the compose engine (PATCH content, `/move`, DELETE) or a `batch` call. For
multi-step requests prefer `POST /admin/compose/{target}/batch`. See
`../oracle-site-compose/SKILL.md`.
