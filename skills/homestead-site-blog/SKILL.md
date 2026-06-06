---
name: homestead-site-blog
description: "Manage the Homestead blog over its API. Triggers: '发博客 / 发一篇博客 / 写篇文章', 'publish a blog', '生成博客 / 今天的博客', 'generate a post', '看最新博客 / 博客列表', 'list/read posts', '把草稿发布 / 更新博客', 'publish draft'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Homestead — Blog

> Prerequisite: read `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API`, auth, and `$HOMESTEAD_SITE_TOKEN`.

## Public (no auth)

```bash
# List published posts
curl -s "$HOMESTEAD_SITE_API/blogs"
# Read one post by slug
curl -s "$HOMESTEAD_SITE_API/blogs/<slug>"
```

## Admin (Bearer token)

```bash
# AI-generate a post. publish=false -> draft. Falls back to deterministic text if DEEPSEEK_API_KEY is unset.
curl -s -X POST "$HOMESTEAD_SITE_API/admin/blogs/generate" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"topic": "optional topic", "publish": false}'

# Create a post manually (title + body_markdown required)
curl -s -X POST "$HOMESTEAD_SITE_API/admin/blogs" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "title": "My Post",
    "body_markdown": "# Hello\n\nBody...",
    "excerpt": "Short summary",
    "tags": ["news"],
    "meta_title": "My Post",
    "meta_description": "SEO description",
    "status": "published"
  }'

# Update a post (partial). e.g. publish a draft:
curl -s -X PATCH "$HOMESTEAD_SITE_API/admin/blogs/<id>" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"status": "published"}'
```

Preserve SEO fields when creating/updating: `title, slug, excerpt, meta_title, meta_description, tags, geo_region`.

## CLI equivalent (on the server, no token needed)

```bash
docker compose exec -T backend flask --app app.main blog generate-daily          # generate + publish
docker compose exec -T backend flask --app app.main blog generate-daily --draft  # generate as draft
```
