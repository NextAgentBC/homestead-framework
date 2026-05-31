---
name: oracle-site-design
description: "Design the Oracle Site's look — interview the user, offer 2-3 style options (Apple-style minimal / Tesla-style bold-dark / editorial), apply one, then fine-tune colors, fonts, hero style, and section content. Triggers: '设计网站 / 换个风格 / 重新设计首页', 'make it like apple / tesla / stripe', '改主题色 / 换配色 / 改颜色', 'design the homepage', 'hero 换成大图 / 居中', '看起来更高级 / 更大胆 / 更简洁', 'generate a design', '分析竞品设计'."
metadata:
  version: 0.2.0
  openclaw:
    category: "website"
    requires:
      bins:
        - curl
---

# Oracle Site — Design (conversational)

> Prerequisite: `../oracle-site-shared/SKILL.md` for `$ORACLE_SITE_API` + `$ORACLE_SITE_TOKEN`.

Design has two layers, both in the active design profile, both render **instantly**:
- **Theme** — `tokens` (colors / fonts / radius / spacing).
- **Composition** — `sections`: an ordered list of `hero`, `features`, `cta`, each with a **variant**.

## Quick recipes (skip the interview when the ask is clear)

**Tesla-style dark** ("改成 Tesla 风" / "make it dark and bold"):
```bash
# 1) bold-dark preset → dark theme + full-bleed hero composition
curl -s -X POST "$ORACLE_SITE_API/admin/design/generate" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" -d '{"preset":"bold-dark"}' >/dev/null
# 2) push to near-black + exact Tesla red (tokens merge; sections kept)
curl -s -X PATCH "$ORACLE_SITE_API/admin/design" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" -d '{"tokens":{"colors":{"paper":"#050505","surface":"#111111","ink":"#ffffff","line":"#262626","primary":"#e82127","accent":"#e82127","link":"#ff5a5f"}}}' >/dev/null
# 3) verify
curl -s "$ORACLE_SITE_API/design" | grep -o '"paper":"#050505"' && curl -s -o /dev/null -w "site %{http_code}\n" https://oracle.nextagent.ca
```
Other one-liners: `{"preset":"minimal"}` (Apple-style light) · `{"preset":"editorial"}` (warm default). All instant, no redeploy.

## Run this as a conversation

1. **Understand the taste.** If the user names a reference site or a vibe, map it (see Reference library). If unclear, ask up to 3 short questions: business/industry? a reference site or feeling (minimal / bold / warm / professional)? light or dark?
2. **Offer 2-3 options**, one line each — preset + hero + palette + why. e.g.
   - *Minimal (Apple-style)* — centered big type, lots of whitespace, neutral + blue. Calm, premium.
   - *Bold Dark (Tesla-style)* — full-bleed dark hero, red accent. Dramatic.
   - *Editorial* — warm split hero. Friendly, content-first.
3. **Apply** the chosen preset:
   ```bash
   curl -s -X POST "$ORACLE_SITE_API/admin/design/generate" \
     -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
     -d '{"preset": "minimal"}'        # minimal | bold-dark | editorial
   ```
4. **Fine-tune** with PATCH (tokens merge; `sections` replaces the whole list):
   ```bash
   # colors
   curl -s -X PATCH "$ORACLE_SITE_API/admin/design" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
     -d '{"tokens": {"colors": {"primary": "#0a6cff", "accent": "#e8505b"}}}'

   # hero variant + real copy, and the rest of the page
   curl -s -X PATCH "$ORACLE_SITE_API/admin/design" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
     -d '{"sections": [
       {"type":"hero","variant":"centered","content":{"kicker":"Accounting","headline":"Books you can trust","subhead":"Calm, accurate bookkeeping for small teams.","cta":{"label":"Book a call","href":"/contact"},"secondaryCta":{"label":"Services","href":"/services"}}},
       {"type":"features","variant":"minimal","content":{"heading":"What we do","items":[{"icon":"shield","title":"Compliance","body":"Filed right, on time."},{"icon":"gauge","title":"Clarity","body":"Numbers you understand."},{"icon":"layers","title":"Scale","body":"Grows with you."}]}},
       {"type":"cta","variant":"banner","content":{"headline":"Ready to tidy your books?","cta":{"label":"Get in touch","href":"/contact"}}}
     ]}'
   ```
5. For a named reference, pull live palette cues then PATCH `tokens`:
   ```bash
   curl -s -X POST "$ORACLE_SITE_API/admin/design/analyze-competitors" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
     -d '{"industry":"...","competitorUrls":["https://apple.com"],"notes":"Inspiration only — create a distinct identity."}'
   ```

## Presets

| preset | vibe | hero | mode |
|---|---|---|---|
| `minimal` | Apple-inspired, calm & premium | centered | light |
| `bold-dark` | Tesla-inspired, dramatic | fullbleed | dark |
| `editorial` | warm, friendly (default) | split | light |

## Modules (section types — compose a page by ordering these in `sections`)

- `hero` — `split` · `centered` · `fullbleed`. content: `badge` (pill), `kicker`, `headline`, `headlineAccent` (gradient-highlighted line), `subhead`, `cta{label,href}`, `secondaryCta`.
- `stats` — KPI bar. content: `items[]{value,label}`.
- `logos` — trust / tech strip. content: `heading`, `items[]{label}`.
- `features` — `cards` · `minimal`. content: `heading`, `subhead`, `items[]{icon,title,body}` (icons: sparkles, mail, shield, gauge, layers, zap, book, cloud).
- `problem` — pain-point cards (accent-toned). content: `heading`, `subhead`, `items[]{icon,title,body}`.
- `comparison` — two-column "usual way vs us". content: `heading`, `left{title,items[]}`, `right{title,items[]}` (right is highlighted).
- `testimonials` — quote cards. content: `heading`, `items[]{quote,author,role}`.
- `pricing` — tier cards. content: `heading`, `subhead`, `items[]{name,price,period,features[],featured,cta{label,href}}`.
- `faq` — native accordion. content: `heading`, `items[]{q,a}`.
- `cta` — `banner`. content: `headline`, `subhead`, `cta{label,href}`.

(The footer is global, multi-column, and built from the site's pages — not a section.)
A strong landing order: **hero → stats → logos → problem → features → comparison → testimonials → pricing → faq → cta**. Use only the modules that fit; drop the rest.

## Reference library

Mapped in `backend/app/data/style_references.json`:
apple / notion / stripe → **minimal** · tesla / linear → **bold-dark** · airbnb → **editorial**.

## Rules
- **Inspiration only — never clone a brand's exact identity or assets.**
- Keep it legible (contrast, spacing). Never hardcode styles in components — everything flows through this API → CSS variables.
- When the user is vague, propose options and confirm before applying a big visual change.
