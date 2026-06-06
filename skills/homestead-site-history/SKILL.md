---
name: homestead-site-history
description: "Undo or roll back website edits — every compose/design change is snapshotted first, so you can undo the last change, browse the history, or restore a page/home/theme to an earlier point. Instant, NO redeploy. Triggers (zh+en): '撤销 / 撤回 / 回退 / 还原 / 改回去 / 恢复上一步', 'undo / undo that / revert / roll back / go back', '回到上一版 / 退回之前的版本 / 历史版本 / 看改动历史', 'restore the previous version / show edit history / version history', '首页改坏了撤销 / 主题换错了 / 把首页恢复 / undo the homepage / revert the theme'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Homestead — History (undo / restore)

> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.

Every edit to a **surface** is snapshotted **before** the change, so a bad edit is never permanent —
**undo** the last change, or **restore** any kept point. Instant, no redeploy. A *surface* (`target`) is:

- `home` — the home page's blocks
- `<page-slug>` — a content page's blocks (e.g. `about`, `services`)
- `design` — the theme (tokens + home sections), snapshotted when you switch / generate a theme

## Undo the last change (the common case)

```bash
# "撤销 / 改回去" — revert the most recent change to the home page
curl -s -X POST "$HOMESTEAD_SITE_API/admin/undo" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"target":"home"}'

# undo the last theme switch
curl -s -X POST "$HOMESTEAD_SITE_API/admin/undo" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" \
  -H "Content-Type: application/json" -d '{"target":"design"}'

# undo on a page — or on its Chinese (/zh) copy
curl -s -X POST "$HOMESTEAD_SITE_API/admin/undo" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" \
  -H "Content-Type: application/json" -d '{"target":"about","locale":"zh"}'
```

Repeated `undo` walks back step by step (each consumes the latest snapshot for that surface).

## Browse history & restore a specific point

```bash
# what changed (newest first): id · surface · label ("add faq", "theme → Saffron") · createdAt
curl -s "$HOMESTEAD_SITE_API/admin/revisions?target=home" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN"
# recent across ALL surfaces (home + every page + design)
curl -s "$HOMESTEAD_SITE_API/admin/revisions" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN"

# jump a surface back to a specific kept snapshot (id from the list above)
curl -s -X POST "$HOMESTEAD_SITE_API/admin/revisions/<id>/restore" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN"
```

`restore` snapshots the *current* state first, so a restore is itself undoable.

## How to respond
1. Confirm the target if unclear ("是首页、某个页面、还是主题?"). Default to `home`.
2. For "撤销 / 改回去 / undo" → `POST /admin/undo` with the target (add `locale:"zh"` if they were editing a `/zh` copy).
3. For "看历史 / 回到某一版" → list `/admin/revisions?target=…`, show the labels + times, then `restore` the one they pick.
4. After undo/restore, confirm what the surface looks like now (e.g. `../homestead-site-compose` list) and reply briefly in the user's language.

Notes:
- History is capped (most recent ~50 per surface + locale); older snapshots are pruned.
- `undo` is per-surface — undoing `home` doesn't touch a page or the theme.
- A theme switch is **one** `design` snapshot (tokens + home sections together) — undoing it restores both.
- Base and `/zh` edits are tracked separately — pass `locale:"zh"` to undo a Chinese-copy edit.
