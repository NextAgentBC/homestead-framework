---
name: oracle-site-block-problem
description: "Problem / pain points block — add or edit a problem / pain points on any Oracle Site page by natural language. Thin recipe over the compose engine (problem). Triggers (zh+en): 加痛点区 / 问题区 / sound familiar / add a problem section."
metadata:
  version: 0.1.0
  generated: true
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Problem / pain points block (`problem`)

> Auto-generated from the block manifest (`GET /api/blocks`). Full engine, rules,
> and edit/move/remove recipes: `../oracle-site-compose/SKILL.md`.
> Prerequisite: `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.

Accent-toned cards naming the pains your offer removes.

- Variants: `cards`
- Content fields: `heading` (text), `subhead` (textarea), `items` (list)

`target` is `home` or a page slug. Adding scaffolds sensible defaults, so the
block looks complete immediately — pass `content` only to override.

```bash
# Add a problem / pain points to the home page
curl -s -X POST "$ORACLE_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"problem","position":"end"}'
```

To **edit / move / remove** an existing one: list blocks to get its id, then use
the compose engine (PATCH content, `/move`, DELETE) or a `batch` call. For
multi-step requests prefer `POST /admin/compose/{target}/batch`. See
`../oracle-site-compose/SKILL.md`.
