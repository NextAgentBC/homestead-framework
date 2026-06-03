---
name: oracle-site-i18n
description: "Translate an Oracle Site into another language (esp. Chinese) — you are the translator. Localizes the home, any page, blog posts, and the UI chrome (nav/footer/buttons) with no redeploy; path-based /zh URLs for SEO. Triggers (zh+en): '把网站/首页/这个页面翻译成中文', 'translate the site/home/this page to Chinese', '加个中文版/做中英双语', 'add a Chinese version / make it bilingual', '改中文导航/页脚/按钮文案', 'fix the Chinese nav/footer labels', '发一篇中文博客 / add a Chinese blog post'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
        - jq
---

# Oracle Site — i18n (you are the translator)

> Prerequisite: `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.

There is **no machine-translation service** — *you* translate. Content is stored per
locale: each entity keeps its default-locale value plus an `i18n` map of overrides.
Routing is path-based: English at `/...`, Chinese at `/zh/...` (good for SEO).
**Theme tokens are global** — translating never changes colors/fonts, only words.

## Locales

```bash
curl -s "$ORACLE_SITE_API/site" | jq '{locales, defaultLocale}'   # e.g. {"locales":["en","zh"],"defaultLocale":"en"}
```
Write to a non-default locale by adding `?locale=zh` to admin writes. Reading content
back: `?locale=zh` on `/design`, `/pages/<slug>`, `/blogs`, `/blogs/<slug>`.

## 1. Translate the home page (the blocks)

`compose` with `?locale=zh` edits the **zh copy** of the page — on first edit it's seeded
from the English blocks (same block ids), so you translate text in place.
```bash
# see the English structure + ids:
curl -s "$ORACLE_SITE_API/admin/compose/home/blocks" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" | jq '.item.blocks'
# translate a block into zh (content deep-merges; only the fields you send change):
curl -s -X PATCH "$ORACLE_SITE_API/admin/compose/home/blocks/b_xxxx?locale=zh" \
  -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"content":{"headline":"你完全拥有的网站","subhead":"每天发布，稳步成长。"}}'
```
Tip: a single `batch?locale=zh` call can translate every block at once. `GET
/admin/surfaces` lists each surface's `locales` so you can see what's already translated.

## 2. Translate a content page

```bash
curl -s -X PATCH "$ORACLE_SITE_API/admin/pages/<id>?locale=zh" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"关于我们","nav_label":"关于","body_markdown":"# 关于我们\n……","meta_title":"关于我们","meta_description":"……"}'
```
(`sections` works here too if the page is block-composed. `nav_order` / `status` /
`show_in_nav` are global — set them without `?locale=`.)

## 3. Translate a blog post

A post is one row served at both `/blog/<slug>` and `/zh/blog/<slug>`; `?locale=zh`
writes the Chinese fields. Create the post first (default locale), then translate:
```bash
curl -s -X PATCH "$ORACLE_SITE_API/admin/blogs/<id>?locale=zh" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"……","excerpt":"……","body_markdown":"……","meta_title":"……","meta_description":"……","tags":["……"]}'
```

## 4. UI chrome strings (nav / footer / buttons)

The frontend ships English + built-in Chinese defaults; override or refine them here
(merges by default; `"replace":true` overwrites):
```bash
curl -s "$ORACLE_SITE_API/i18n/zh" | jq '.item.messages'      # current zh overrides (public)
curl -s -X PATCH "$ORACLE_SITE_API/admin/i18n/zh" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"messages":{"nav.blog":"博客","nav.contact":"联系我们","footer.more":"更多"}}'
```
Common keys: `nav.blog` `nav.contact` · `home.latest` `home.read` · `blog.title` ·
`contact.title` `contactForm.send` · `footer.pages` `footer.more` `footer.tagline`.

## Rules
- You are the translator — write natural, idiomatic Chinese, not literal word-for-word.
- Don't touch tokens here (global). Use `../oracle-site-design` for look, this for language.
- Translate *content* (blocks/pages/posts) **and** *chrome* (UI messages) for a complete locale.
- Untranslated fields automatically fall back to the default locale — safe to translate incrementally.
- Translate **in place on the same block ids** — never add/remove/reorder blocks in a locale (that makes en/zh structurally diverge). Layout is shared; only words change.
- **Verify completeness:** after translating, run `GET /admin/consistency` and clear every `missing_translation` / `language_mismatch` finding before telling the user it's done.
