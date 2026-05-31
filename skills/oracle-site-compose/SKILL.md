---
name: oracle-site-compose
description: "Compose and edit any Oracle Site page from blocks by natural language — add / move / edit / remove / duplicate sections on the home page or any page, one block at a time. Manifest-driven: discovers the available blocks from the API and validates before writing. Triggers (zh+en): '加一个模块/板块/section', 'add a pricing section / add testimonials / add an FAQ', '把 FAQ 移到 pricing 上面 / reorder / move ... above/below', '改第N个/把标题改成/改文案/change the headline/换个布局变体', '删掉那个板块/去掉 logo 墙/remove the ...', '复制那个板块/duplicate', '首页有哪些模块/这个页面结构/list blocks', '有哪些可用 block/what blocks can I add'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
        - jq
---

# Oracle Site — Compose (block-level page editing)

> Prerequisite: `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.

Every page is an ordered list of **blocks** — `{id, type, variant, content}`. This skill edits that list **one block at a time, by stable id**, on:

- **`home`** — the home page (the active design profile), or
- **`<page-slug>`** — any page, e.g. `about`, `services`.

Theme (colors / fonts / template) is a different skill — `oracle-site-design`. This one is **structure**: which blocks, in what order, with what content.

## 1. Discover, then list (do this before any edit)

Catalog — what blocks exist, their variants and fields (public, no token):
```bash
curl -s "$ORACLE_SITE_API/blocks" | jq '.items[] | {type, variants, fields: [.fields[].key]}'
```
Current blocks on a target — **get the ids you'll edit**:
```bash
curl -s "$ORACLE_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" | jq '.item.blocks'
# -> [{ "id":"b_1a2b3c4d", "type":"hero", "variant":"centered", "title":"...", "items":null }, ...]
```

## 2. Edit recipes

Every write returns `{ "item": <the block>, "page": { "blocks": [...] } }` so you can confirm.

**Add** — `position` is `start` | `end` | an index | `after:<id>` | `before:<id>`. A new block is scaffolded with sensible defaults, so it looks complete immediately; pass `content` to override:
```bash
curl -s -X POST "$ORACLE_SITE_API/admin/compose/home/blocks" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"testimonials","position":"after:b_1a2b3c4d","content":{"heading":"Loved by teams"}}'
```

**Edit** — `content` deep-merges; pass `"replaceContent":true` to overwrite; `variant` changes the layout:
```bash
curl -s -X PATCH "$ORACLE_SITE_API/admin/compose/home/blocks/b_1a2b3c4d" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"variant":"centered","content":{"headline":"Books you can trust"}}'
```

**Move / Duplicate / Remove**:
```bash
curl -s -X POST   "$ORACLE_SITE_API/admin/compose/home/blocks/b_1a2b3c4d/move"      -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" -d '{"position":"before:b_5e6f7a8b"}'
curl -s -X POST   "$ORACLE_SITE_API/admin/compose/home/blocks/b_1a2b3c4d/duplicate" -H "Authorization: Bearer $ORACLE_SITE_TOKEN"
curl -s -X DELETE "$ORACLE_SITE_API/admin/compose/home/blocks/b_1a2b3c4d"           -H "Authorization: Bearer $ORACLE_SITE_TOKEN"
```

## 3. Editing a single item inside a list (important)

Nested **objects** merge (e.g. `content.cta`), but **arrays replace wholesale** (e.g. `content.items`, a tier's `features`). To change "the 2nd pricing tier price", read the block, edit the array, send it back:
```bash
ITEMS=$(curl -s "$ORACLE_SITE_API/admin/compose/home/blocks" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" \
  | jq -c '.item.blocks')              # find the pricing block id first, then read full content via list
# read full content of one block is via the page list above; edit the items array, then:
curl -s -X PATCH "$ORACLE_SITE_API/admin/compose/home/blocks/b_pricing01" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"content":{"items":[ ...full edited items array... ]}}'
```

## 4. Rules
- **Discover before you write.** Use real `type` / `variant` values from `/blocks` and real ids from the target's list. Unknown type/variant/id or a bad `position` returns a clear `error.message` — read it and retry.
- **Objects merge, arrays replace.** For list edits: read → modify the array → send it back.
- Edits are **instant** — live site updates on next load, no redeploy.
- Available block types (P1): `hero` · `stats` · `logos` · `features` · `problem` · `comparison` · `testimonials` · `pricing` · `faq` · `cta`. The catalog is the source of truth; new types appear there as they're added.
- A **brand-new block type** (not an instance of an existing one) is a code change — add it to `backend/app/services/block_service.py` (manifest) **and** a renderer in `frontend/components/sections.tsx`, then redeploy. After that it shows up in `/blocks` automatically.
