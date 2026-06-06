---
name: homestead-site-block-team
description: "Team block — add or edit a team on any Homestead page by natural language. Thin recipe over the compose engine (team). Triggers (zh+en): 加团队介绍 / 成员 / 我们的团队 / add a team section / members."
metadata:
  version: 0.1.0
  generated: true
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Team block (`team`)

> Auto-generated from the block manifest (`GET /api/blocks`). Full engine, rules,
> and edit/move/remove recipes: `../homestead-site-compose/SKILL.md`.
> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.

Team member cards — name, role, optional photo (image URL) and short bio.

- Variants: `cards`
- Content fields: `heading` (text), `subhead` (textarea), `items` (list)

`target` is `home` or a page slug. Adding scaffolds sensible defaults, so the
block looks complete immediately — pass `content` only to override.

```bash
# Add a team to the home page
curl -s -X POST "$HOMESTEAD_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"team","position":"end"}'
```

To **edit / move / remove** an existing one: list blocks to get its id, then use
the compose engine (PATCH content, `/move`, DELETE) or a `batch` call. For
multi-step requests prefer `POST /admin/compose/{target}/batch`. See
`../homestead-site-compose/SKILL.md`.
