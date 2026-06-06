#!/usr/bin/env python3
"""Generate one thin "block = skill" per block type from the live block catalog.

Source of truth is GET /api/blocks (the manifest). Each generated skill is a
discoverable trigger surface (so "加个价格表" / "add an FAQ" routes precisely);
the actual work is delegated to the homestead-site-compose engine — no duplicated
CRUD logic. Re-run this whenever the block library changes; new types appear in
/api/blocks automatically and get a skill here.

Usage:
    python3 skills/generate-block-skills.py [API_BASE]
    API_BASE defaults to $HOMESTEAD_SITE_API or http://127.0.0.1:8000/api
"""
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("HOMESTEAD_SITE_API") or "http://127.0.0.1:8000/api").rstrip("/")

# Bilingual trigger phrases per known type; generic fallback for new types.
TRIGGERS = {
    "hero": "加个 hero / 改首屏标题 / 改大标题 / add a hero / change the headline / hero 换居中或大图",
    "stats": "加一排数据 / KPI / 指标条 / add stats / metrics row / 改数字",
    "logos": "加 logo 墙 / 合作伙伴 / 技术栈条 / add a logo or trust strip",
    "features": "加功能区 / 我们能做什么 / 卖点 / add features / what-we-do / 改某个卖点",
    "problem": "加痛点区 / 问题区 / sound familiar / add a problem section",
    "comparison": "加对比 / 我们 vs 别人 / before after / add a comparison table",
    "testimonials": "加评价 / 用户证言 / 口碑 / add testimonials / quotes",
    "pricing": "加价格表 / 套餐 / 定价 / add pricing / tiers / 改某档价格",
    "faq": "加 FAQ / 常见问题 / 问答 / add an FAQ / questions",
    "cta": "加行动号召 / CTA / 引导按钮区 / add a CTA banner",
    "section": "加一个自定义板块 / 照着截图做个 section / 柔性板块 / custom section / build from a screenshot / flexible block",
    "steps": "加步骤区 / 流程 / 操作步骤 / 怎么做 / add steps / how it works / process",
    "gallery": "加图库 / 图片网格 / 相册 / 作品集图 / add a gallery / image grid",
    "team": "加团队介绍 / 成员 / 我们的团队 / add a team section / members",
    "banner": "加横幅 / 公告条 / 提示条 / 促销条 / add a banner / announcement strip",
}


def field_summary(fields):
    parts = []
    for f in fields or []:
        k, t = f.get("key"), f.get("type")
        parts.append(f"`{k}`" + (f" ({t})" if t else ""))
    return ", ".join(parts) if parts else "—"


def render(block, icons):
    t = block["type"]
    label = block.get("label", t.title())
    desc = block.get("description", "")
    variants = block.get("variants", []) or []
    triggers = TRIGGERS.get(t, f"加一个{label} / add a {label} / 改{label} / edit the {label}")
    icon_note = ""
    if any((f.get("type") == "icon") for f in block.get("fields", [])):
        icon_note = f"\n- Icons: {', '.join(icons)}"
    variants_line = " · ".join(f"`{v}`" for v in variants) if variants else "`default`"

    return f"""---
name: homestead-site-block-{t}
description: "{label} block — add or edit a {label.lower()} on any Homestead page by natural language. Thin recipe over the compose engine ({t}). Triggers (zh+en): {triggers}."
metadata:
  version: 0.1.0
  generated: true
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# {label} block (`{t}`)

> Auto-generated from the block manifest (`GET /api/blocks`). Full engine, rules,
> and edit/move/remove recipes: `../homestead-site-compose/SKILL.md`.
> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.

{desc}

- Variants: {variants_line}
- Content fields: {field_summary(block.get('fields'))}{icon_note}

`target` is `home` or a page slug. Adding scaffolds sensible defaults, so the
block looks complete immediately — pass `content` only to override.

```bash
# Add a {label.lower()} to the home page
curl -s -X POST "$HOMESTEAD_SITE_API/admin/compose/home/blocks" \\
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \\
  -d '{{"type":"{t}","position":"end"}}'
```

To **edit / move / remove** an existing one: list blocks to get its id, then use
the compose engine (PATCH content, `/move`, DELETE) or a `batch` call. For
multi-step requests prefer `POST /admin/compose/{{target}}/batch`. See
`../homestead-site-compose/SKILL.md`.
"""


def main():
    url = f"{API}/blocks"
    with urllib.request.urlopen(url, timeout=10) as r:
        data = json.load(r)
    items = data.get("items", [])
    icons = data.get("icons", [])
    if not items:
        print(f"No blocks returned from {url}", file=sys.stderr)
        return 1
    written = []
    for block in items:
        t = block["type"]
        d = os.path.join(HERE, f"homestead-site-block-{t}")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(render(block, icons))
        written.append(t)
    print(f"Generated {len(written)} block skills from {url}: {', '.join(written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
