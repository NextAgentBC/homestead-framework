---
name: website
description: "Oracle Site control center — the categorized command menu for managing the website (content / design / language / ops). Trigger ONLY on the command or an explicit ask for the menu: '/website', '网站命令 / 网站菜单 / 有哪些命令 / 网站怎么改 / 管理网站', 'website commands / website menu / what can I do with the site / manage the site'. Do not trigger on general website chatter. Shows the grouped list and routes to the matching oracle-site-* skill."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Oracle Site — Control Center  (`/website`)

The website's operations are split across focused skills (each is also its own
Telegram command). This is the **categorized front door**: when the user sends
`/website` or asks "网站有哪些命令 / 怎么管理网站 / website menu", show the grouped
menu below (trim to what's relevant, keep it bilingual and short), then **delegate
to the matching skill** for whatever they pick — don't re-implement, route.

> Live site: **oracle.nextagent.ca** · API: **oracle-api.nextagent.ca**. Any change
> needs `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.
> All edits are **instant, no redeploy** (except a brand-new coded block type).

## 📝 内容 · Content
- **/oracle_site_blog** — 写 / 生成 / 发布 / 改博客 · write, generate, publish, edit posts
- **/oracle_site_pages** — 新建 / 修改页面(关于、服务、隐私…)· create & edit pages
- **/oracle_site_newsletter** — 订阅者 / 联系表单 · newsletter & contact form
- **/oracle_site_media** — 上传图片 → 用到图库 / 团队 / 博客 · upload a photo, use it on the site

## 🎨 设计 · Design
- **/oracle_site_design** — 换模板(共 18 套)/ 改配色 / 改字体 / 改 hero · templates · colors · fonts
- **/oracle_site_capture** — 发一张截图 → 自动重建成板块(同化成本站风格)· screenshot → section
- **/oracle_site_compose** — 给某页加 / 改 / 移 / 删 / 复制板块 · add·edit·move·remove blocks

## 🌐 双语 · Language (中 / EN)
- **/oracle_site_i18n** — 把首页 / 某个页面 / 某篇博客翻成中文(或其它语言)· translate content + UI

## ⚙️ 运维 · Ops
- **/oracle_site_ops** — 网站状态 / 日志 / 重新部署 / 重启 · status · logs · redeploy

## How to respond
1. On `/website` (or a menu ask): print the categories above, trimmed, and ask
   **"想做哪一类?(内容 / 设计 / 双语 / 运维)"**.
2. When the user names a task (or taps a sub-command), **invoke the matching
   `oracle-site-*` skill** — its own triggers already cover the phrasing. Read its
   SKILL.md, don't duplicate its logic here.
3. For anything that writes, ensure the admin token is available first
   (`../oracle-site-shared/SKILL.md`).
4. Keep replies short and in the user's language (Chinese by default here).
