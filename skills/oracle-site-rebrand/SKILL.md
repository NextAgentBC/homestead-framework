---
name: oracle-site-rebrand
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

> Prerequisite: `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.

Switching industry is a **site-level** change — it must cascade to the home, every
page, and every locale, or you get the classic mess: English page showing Chinese,
the zh page stuck on the old industry, pages inconsistent with the home. This skill
gives you one atomic operation plus a **machine-checkable definition of done** so you
finish the job instead of stopping halfway.

The golden rule: **you are not done until `GET /admin/consistency` returns `ok: true`.**

## 1. See what's wrong now (optional but smart)

```bash
curl -s "$ORACLE_SITE_API/admin/consistency" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" | jq '.item.summary, .item.findings'
```

## 2. Rebrand (one atomic call)

```bash
# preview first if unsure (no writes):
curl -s -X POST "$ORACLE_SITE_API/admin/site/rebrand" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" \
  -H "Content-Type: application/json" -d '{"industry":"beauty","dryRun":true}' | jq '.item, .audit.summary'

# do it (regenerates home design+sections for the industry, DROPS stale per-locale
# section overrides on the home AND every page so nothing old/mixed survives,
# snapshots each surface — one undo reverts the whole rebrand — and returns the audit):
curl -s -X POST "$ORACLE_SITE_API/admin/site/rebrand" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" \
  -H "Content-Type: application/json" -d '{"industry":"beauty"}' | jq '.item.industry, .pagesTouched, .audit.summary'
```

Body: `{ "industry": "beauty" }` (or `"preset"` for a named style; optional
`"competitorUrls":[...]`, `"brandName":"..."`, `"dryRun":true`). Valid industries map
to the 18 templates (see `oracle-site-design`). This is a **rebrand, not a tweak** — it
regenerates the home and resets localized section copy on purpose.

## 2a. Imagery — placeholders by default, generation optional

Template image slots ship **empty on purpose**. With no image, each one renders a
**designed placeholder showing its prompt** (`imagePrompt` on the block) — so even with
**no image generator** (the usual case for students) the page looks intentional and says
exactly what photo goes where. **That's the default; you don't have to do anything.**
The user replaces a slot with a real photo later (upload via `oracle-site-media`) and the
placeholder disappears.

**Only if you have an image generator** (e.g. openart on this host) and want real photos
now: the rebrand response hands you `imagery: { style, images: [ {block, item?, field,
aspect, prompt} ] }` — generate each and attach it:

```bash
RB=$(curl -s -X POST "$ORACLE_SITE_API/admin/site/rebrand" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" \
       -H "Content-Type: application/json" -d '{"industry":"beauty"}')
STYLE=$(echo "$RB" | jq -r '.imagery.style')
echo "$RB" | jq -c '.imagery.images[]' | while read -r spec; do
  PROMPT="$(echo "$spec" | jq -r .prompt), $STYLE"; ASPECT=$(echo "$spec" | jq -r .aspect)
  BLOCK=$(echo "$spec" | jq -r .block); FIELD=$(echo "$spec" | jq -r .field); ITEM=$(echo "$spec" | jq -r '.item // empty')
  # 1) generate (openart-image skill; runs on this host) → 2) upload → absolute URL
  IMG=$(node ~/.claude/skills/openart-image/cli.js "$PROMPT" --aspect "$ASPECT" --quality low --out /tmp/rb.png | tail -1)
  URL=$(curl -s -X POST "$ORACLE_SITE_API/admin/media" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -F "file=@${IMG}" | jq -r .item.url)
  # 3) PATCH the target block's image field (top-level field, or items[ITEM].field)
  if [ -n "$ITEM" ]; then BODY=$(jq -nc --arg u "$URL" --argjson i "$ITEM" '{content:{items:({} )}}'); fi
  curl -s -X PATCH "$ORACLE_SITE_API/admin/compose/home/blocks/$BLOCK" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" \
    -H "Content-Type: application/json" -d "$(jq -nc --arg u "$URL" --arg f "$FIELD" '{content:{($f):$u}}')"
done
```

For list items (`item` set, e.g. gallery), patch that item's image — easiest is to GET the
block, set `content.items[ITEM].image = URL`, and PATCH the whole `content` back (deep-merge
replaces the list). See `oracle-site-media` for the media API and `oracle-site-compose` for
block edits. If `flux-image` is down, `openart-image` is the generator (gpt-image-2).

## 3. Finish the work the audit lists (this is the real job)

The rebrand sets up clean structure + theme, but the home now carries **template copy**
and the pages still carry the **old industry's copy** — so the audit will show findings.
Work them down by kind:

- **language_mismatch / template copy on the home** → rewrite the home blocks into real
  copy for this business in the **default locale (en)**, in English. Use `oracle-site-compose`
  (`batch` is fastest). Add real imagery (hero/cta/gallery `image` fields) via
  `oracle-site-media` — a proper site has photos, not empty blocks.
- **pages still old-industry (`industry_residue`)** → rewrite each page's blocks/markdown
  for the new industry, both locales (`oracle-site-compose` / `oracle-site-pages`).
- **missing_translation** → translate every surface into each non-default locale with
  `oracle-site-i18n` (`compose ...?locale=zh`, `pages ...?locale=zh`). Translate in place
  on the **same block ids** — never restructure a locale (that causes `structural_drift`).
- **structural_drift** → the locale's block list diverged from base; re-translate from the
  base block ids instead of keeping an old localized structure.

Also set the brand chrome: `brandName` on rebrand sets the design name, but the nav/footer
brand is `SITE_NAME` (backend `.env`) — if it still shows the old brand, update env + redeploy.

## 4. Loop until clean — then you're done

```bash
curl -s "$ORACLE_SITE_API/admin/consistency" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" | jq '.item.ok, .item.summary.byKind'
```

Repeat step 3 → re-audit until `ok: true`. **Do not tell the user the site is done while
any findings remain.** Then verify the public site renders (both locales) before reporting.

## Rules

- One industry switch = `rebrand` once, then finish copy + translation + images, then audit-clean.
- Default locale (en) text must be in English; zh text must be in Chinese. The audit enforces this.
- Every surface (home + all pages) must exist and be coherent in **every** locale.
- A real site has imagery. Don't ship empty hero/gallery blocks — generate + attach photos.
