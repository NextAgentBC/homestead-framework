---
name: homestead-site-media
description: "Host a user-uploaded image on the Homestead and use it in a page — upload a photo, get a /api/media/<file> URL, drop it into a gallery / team / testimonial / flexible section block or a blog/page body. Upload-only — no image generation. Triggers (zh+en): '上传这张图/把这张图放上去/加到图库/gallery 加图', '这是我们团队的照片/给这个成员配头像/team 配图', '给这篇博客配张图/文章里插张图', 'upload this image / use this photo / add it to the gallery / put this on the page', 'host this picture / add a team photo / a headshot / a blog image', '我有张图想放网站上'."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
        - jq
---

# Homestead — Media (upload a photo, use it on the site)

> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.
> Structure edits go through `../homestead-site-compose/SKILL.md`.

The user hands you an **image** (e.g. a photo sent in Telegram). You **host it** on the
site and use its URL in a block or a post. This is **upload-only** — there is no image
generation. Supported: **png · jpg · gif · webp**, up to **10 MB**.

## First: is this a photo to show, or a design to copy?

- **A real photo to display as-is** — a team headshot, a product/food shot, a blog image →
  **upload it** (this skill). It gets hosted and shown exactly as given.
- **A screenshot of some website's section the user wants to *replicate*** → **do not upload it.**
  You *look* at it and rebuild the layout in the site's own tokens — see
  `../homestead-site-capture/SKILL.md`. That's assimilation (your colors/fonts), not a pixel copy.

When in doubt, ask one line: "把这张图放到网站上展示,还是照着它的版式做一个板块?"

## 1. Upload (three ways — pick what you have)

Every upload returns `{ "item": { "filename", "url", "path", "bytes", "contentType" } }`.
Use **`url`** — a full absolute URL (`https://…/api/media/<file>`). It's ready to drop straight
into an `<img>` field or Markdown. (The frontend host has no `/api` proxy, so a bare
`/api/media/…` path won't load there — always use the absolute `url`.)

```bash
# (a) a local file you were given (the usual case)
curl -s -X POST "$HOMESTEAD_SITE_API/admin/media" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" \
  -F "file=@/path/to/photo.jpg"

# (b) fetch from a URL the user pasted
curl -s -X POST "$HOMESTEAD_SITE_API/admin/media" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/their-photo.jpg"}'

# (c) inline base64 (data: URLs are fine too)
curl -s -X POST "$HOMESTEAD_SITE_API/admin/media" \
  -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"data":"<base64-bytes>","filename":"headshot.png"}'
```
The bytes are checked by magic number — a non-image (or a renamed `.exe`) is rejected with
`400`; too large is `413`. Grab the URL for the next step:
```bash
URL=$(curl -s -X POST "$HOMESTEAD_SITE_API/admin/media" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -F "file=@photo.jpg" | jq -r '.item.url')
```

## 2. Use the URL on the site

Images live in these places (set the `image` field to the uploaded `url`):

**Gallery** (a grid of photos):
```bash
curl -s -X POST "$HOMESTEAD_SITE_API/admin/compose/home/blocks" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"gallery","content":{"heading":"Our space","items":[
       {"image":"'"$URL"'","caption":"Front room"} ]}}'
```
**Team** — `items[].image` is the member photo. **Testimonials** — `items[].image` is the author avatar.
Edit an existing block: read its `items` array, set `image` on the right entry, PATCH it back
(arrays replace wholesale — see the compose skill).

**Flexible `section`** — a `media` item: `{"kind":"media","image":"<url>","title":"…"}` (see capture skill).

**Inside a blog post or page body** — Markdown, anywhere in `body_markdown`:
```markdown
![Alt text that describes the photo](/api/media/your-file.png)
```
(There's no separate "cover image" field — the blog hero image is just the first Markdown
image in the body. Update via `PATCH /admin/blogs/{id}` with the edited `body_markdown`.)

Always write **real alt/caption text** — it's the accessibility + SEO description of the photo.

## 3. Manage what's hosted

```bash
curl -s "$HOMESTEAD_SITE_API/admin/media" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" | jq '.items'   # list (name, url, bytes)
curl -s -X DELETE "$HOMESTEAD_SITE_API/admin/media/<filename>" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN"  # remove one
```
Reuse before re-uploading: if the photo's already in the list, just use its `url`.

## Rules
- **Upload-only, no generation.** If the user wants an *illustration made*, say it's not wired up
  (images are user-supplied); offer to use a photo they provide or a public image URL.
- png/jpg/gif/webp, ≤ 10 MB. Other types/oversized are rejected with a clear `error.message` — read it.
- Use the returned **absolute `url`** verbatim — don't hand-build or shorten it (the frontend can't serve a bare `/api/media/…` path; only the API host does).
- A *screenshot to replicate a layout* is a capture job, not an upload — `../homestead-site-capture/SKILL.md`.
- Don't host copyrighted/3rd-party images you don't have rights to. Inspiration ≠ reuse.
