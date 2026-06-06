---
name: homestead-site-rebrand
description: "Switch the whole Homestead site to a new industry COHERENTLY — one atomic op + a consistency audit you loop on until clean, so you never leave a half-rebranded, mixed-language, inconsistent site. Use when the user says: '把网站改成美容院/餐厅/律所/诊所官网', 'turn the site into a <industry> site', '换个行业 / 整站重做成 X 行业', 'rebrand the site to X', '换成美容/医美风格的官网'. After it, you finish copy + translation + images guided by the audit."
metadata:
  version: 0.1.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
        - jq
---

# Homestead — Rebrand to a new industry (do it COMPLETELY)

> Prerequisite: `../homestead-site-shared/SKILL.md` for `$HOMESTEAD_SITE_API` + `$HOMESTEAD_SITE_TOKEN`.

Switching industry is a **site-level** change — it must cascade to the home, every
page, and every locale, or you get the classic mess: English page showing Chinese,
the zh page stuck on the old industry, pages inconsistent with the home. This skill
gives you one atomic operation plus a **machine-checkable definition of done** so you
finish the job instead of stopping halfway.

The golden rule: **you are not done until `GET /admin/consistency` returns `ok: true`.**

## 1. See what's wrong now (optional but smart)

```bash
curl -s "$HOMESTEAD_SITE_API/admin/consistency" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" | jq '.item.summary, .item.findings'
```

## 2. Rebrand (one atomic call)

```bash
# preview first if unsure (no writes):
curl -s -X POST "$HOMESTEAD_SITE_API/admin/site/rebrand" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" \
  -H "Content-Type: application/json" -d '{"industry":"beauty","dryRun":true}' | jq '.item, .audit.summary'

# do it (regenerates the home design+sections for the industry; updates the site
# IDENTITY in the DB — industry now, brand + audience if you pass them — so nav/
# footer brand, blog lede, SEO and the chat assistant all switch with NO redeploy;
# rebuilds the About/Services starter pages from templates for the new theme; DROPS
# stale per-locale section overrides on the home AND every page; snapshots each
# surface — one undo reverts the whole rebrand — and returns the audit):
curl -s -X POST "$HOMESTEAD_SITE_API/admin/site/rebrand" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" \
  -H "Content-Type: application/json" -d '{"industry":"beauty","brandName":"Lumière","audience":"skincare clients"}' \
  | jq '.item.industry, .site, .pagesTouched, .audit.summary'
```

Body: `{ "industry": "beauty" }` (or `"preset"` for a named style; optional
`"brandName":"..."`, `"audience":"..."`, `"competitorUrls":[...]`, `"dryRun":true`).
`brandName` sets the brand **and** the chat assistant's name; `audience` retargets the
blog lede + chat. Valid industries map to the 18 templates (see `homestead-site-design`).
This is a **rebrand, not a tweak** — it regenerates the home, updates the site identity,
and resets localized section copy on purpose.

## 2a. Imagery — placeholders by default, generation optional

Template image slots ship **empty on purpose**. With no image, each one renders a
**designed placeholder showing its prompt** (`imagePrompt` on the block) — so even with
**no image generator** (the usual case for students) the page looks intentional and says
exactly what photo goes where. **That's the default; you don't have to do anything.**
The user replaces a slot with a real photo later (upload via `homestead-site-media`) and the
placeholder disappears.

**Only if you have an image generator** (e.g. openart on this host) and want real photos
now: the rebrand response hands you `imagery: { style, images: [ {block, item?, field,
aspect, prompt} ] }` — generate each and attach it:

```bash
RB=$(curl -s -X POST "$HOMESTEAD_SITE_API/admin/site/rebrand" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" \
       -H "Content-Type: application/json" -d '{"industry":"beauty"}')
STYLE=$(jq -r '.imagery.style' <<<"$RB")
echo "$RB" | jq -c '.imagery.images[]' | while read -r spec; do
  BLOCK=$(jq -r .block <<<"$spec"); FIELD=$(jq -r .field <<<"$spec")
  ITEM=$(jq -r '.item // "none"' <<<"$spec"); ASPECT=$(jq -r .aspect <<<"$spec")
  # 1) generate (openart-image; runs on this host) → 2) upload → absolute URL
  IMG=$(node ~/.claude/skills/openart-image/cli.js "$(jq -r .prompt <<<"$spec"), $STYLE" --aspect "$ASPECT" --quality low --out /tmp/rb.png | tail -1)
  URL=$(curl -s -X POST "$HOMESTEAD_SITE_API/admin/media" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" -F "file=@${IMG}" | jq -r .item.url)
  # 3) build the PATCH body, then attach
  if [ "$ITEM" = "none" ]; then                       # hero / cta — a top-level field (content deep-merges)
    BODY=$(jq -nc --arg u "$URL" --arg f "$FIELD" '{content:{($f):$u}}')
  else                                                 # gallery item — read the block's full items, set one image, send the whole list back
    ITEMS=$(curl -s "$HOMESTEAD_SITE_API/design" | jq -c --arg id "$BLOCK" --arg u "$URL" --argjson i "$ITEM" \
              '(.item.sections[]|select(.id==$id)|.content.items) | .[$i].image=$u')
    BODY=$(jq -nc --argjson items "$ITEMS" '{content:{items:$items}}')
  fi
  curl -s -X PATCH "$HOMESTEAD_SITE_API/admin/compose/home/blocks/$BLOCK" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" \
    -H "Content-Type: application/json" -d "$BODY" >/dev/null
done
```

Why two branches: a top-level field (hero/cta `image`) deep-merges, but a gallery item lives in
a list — deep-merge replaces lists wholesale, so you must send the **full** `items` array with
the one image set (read it from `/design`). See `homestead-site-media` (media API) and
`homestead-site-compose` (block edits). `flux-image` is an alternative generator if available.

## 3. Finish the work the audit lists (this is the real job)

The rebrand sets up clean structure + theme, but the home now carries **template copy**
and the pages still carry the **old industry's copy** — so the audit will show findings.
Work them down by kind:

- **language_mismatch / template copy on the home** → rewrite the home blocks into real
  copy for this business in the **default locale (en)**, in English. Use `homestead-site-compose`
  (`batch` is fastest). Add real imagery (hero/cta/gallery `image` fields) via
  `homestead-site-media` — a proper site has photos, not empty blocks.
- **pages still old-industry (`industry_residue`)** → rewrite each page's blocks/markdown
  for the new industry, both locales (`homestead-site-compose` / `homestead-site-pages`).
- **missing_translation** → translate every surface into each non-default locale with
  `homestead-site-i18n` (`compose ...?locale=zh`, `pages ...?locale=zh`). Translate in place
  on the **same block ids** — never restructure a locale (that causes `structural_drift`).
- **structural_drift** → the locale's block list diverged from base; re-translate from the
  base block ids instead of keeping an old localized structure.

Brand chrome updates automatically — no redeploy. The rebrand writes the site identity to
the DB (SiteSettings): `industry` always, and `brandName` → brand name **and** chat-assistant
name, `audience` → audience. Nav/footer brand, blog lede, SEO and the chat persona all read it
live. Fine-tune anything afterwards with
`PATCH /admin/site/settings {siteName?, industry?, audience?, region?, assistantName?}`.

## 4. Loop until clean — then you're done

```bash
curl -s "$HOMESTEAD_SITE_API/admin/consistency" -H "Authorization: Bearer $HOMESTEAD_SITE_TOKEN" | jq '.item.ok, .item.summary.byKind'
```

Repeat step 3 → re-audit until `ok: true`. **Do not tell the user the site is done while
any findings remain.** Then verify the public site renders (both locales) before reporting.

## Rules

- One industry switch = `rebrand` once, then finish copy + translation + images, then audit-clean.
- Default locale (en) text must be in English; zh text must be in Chinese. The audit enforces this.
- Every surface (home + all pages) must exist and be coherent in **every** locale.
- A real site has imagery. Don't ship empty hero/gallery blocks — generate + attach photos.
