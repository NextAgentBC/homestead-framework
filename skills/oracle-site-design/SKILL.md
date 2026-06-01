---
name: oracle-site-design
description: "Design the Oracle Site's look — interview the user, offer style options from 18 templates (base: minimal / bold-dark / editorial / corporate · industry: tech / healthcare / restaurant / realestate / fitness / beauty / legal / creative · style: luxe / education / nonprofit / finance / playful / neon), apply one, then fine-tune colors, fonts, hero style, content width (wide/narrow), and section content. Triggers: '设计网站 / 换个风格 / 重新设计首页', 'make it like apple / tesla / stripe', '做个餐厅网站 / 健身房风格 / 律所网站 / 美容院风格', 'a site for a clinic / gym / cafe / law firm', '改主题色 / 换配色 / 改颜色', 'design the homepage', 'hero 换成大图 / 居中', '看起来更高级 / 更大胆 / 更简洁', '调宽一点 / 窄一点 / 宽屏 / 全宽 / make it wider / narrower', 'generate a design', '分析竞品设计'."
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
- **Theme** — `tokens` (colors / fonts / radius / spacing). `tokens.colors` keys: `ink` · `muted` · `paper` · `surface` · `line` · `primary` · `accent` · `highlight` · `link`, plus three for the dark "contrast band" (full-bleed hero + CTA banner): `surfaceInverse` (band background), `inkInverse` (text on it), `onPrimary` (text/icon on primary-filled buttons — set dark when `primary` is light). Nothing is hard-coded in components; every surface is a token.
- **Composition** — `sections`: an ordered list of `hero`, `features`, `cta`, each with a **variant**.

## Quick recipes (skip the interview when the ask is clear)

**Tesla-style dark** ("改成 Tesla 风" / "make it dark and bold"):
```bash
# 1) bold-dark preset → dark theme + full-bleed hero composition
curl -s -X POST "$ORACLE_SITE_API/admin/design/generate" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" -d '{"preset":"bold-dark"}' >/dev/null
# 2) push to near-black + exact Tesla red (tokens merge; sections kept)
curl -s -X PATCH "$ORACLE_SITE_API/admin/design" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" -d '{"tokens":{"colors":{"paper":"#050505","surface":"#111111","ink":"#ffffff","line":"#262626","primary":"#e82127","accent":"#e82127","link":"#ff5a5f"}}}' >/dev/null
# 3) verify
curl -s "$ORACLE_SITE_API/design" | grep -o '"paper":"#050505"' && curl -s -o /dev/null -w "site %{http_code}\n" https://homestead.nextagent.ca
```
Other one-liners: `{"preset":"minimal"}` (Aurora, light) · `{"preset":"editorial"}` (Atelier, warm serif) · `{"preset":"corporate"}` (Meridian, B2B navy) · plus eight industry templates — `tech` · `healthcare` · `restaurant` · `realestate` · `fitness` · `beauty` · `legal` · `creative` (see the Presets table). Or skip the preset and pass `{"industry":"dental"|"gym"|"law"|…}` to auto-pick one. All instant, no redeploy.

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
     -d '{"preset": "minimal"}'        # any key from the Presets table, or {"industry":"<name>"}
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

## Presets (eighteen switchable templates)

Each is a full template — palette + light/dark mode + font pairing + hero style + section composition — not just a recolor. Switch with one `generate` call (`{"preset":"<key>"}`); renders instantly.

| preset | name | vibe | hero | mode | font |
|---|---|---|---|---|---|
| `minimal` | Aurora | Apple / Linear / Stripe — calm, premium, spacious | centered | light | Inter |
| `bold-dark` | Eclipse | Tesla / Vercel — dramatic, high-contrast, electric violet | fullbleed | dark | Space Grotesk |
| `editorial` | Atelier | warm, literary — serif display, drop-cap long-form | split | light | Spectral serif |
| `corporate` | Meridian | trustworthy B2B — structured navy, pricing tiers | split | light | Space Grotesk |
| `tech` | Nimbus | modern SaaS / startup — indigo + cyan, geometric | centered | light | Space Grotesk |
| `healthcare` | Vitalis | calm clinic / wellness — teal, rounded, trustworthy | split | light | Inter |
| `restaurant` | Saffron | warm restaurant / café — paprika + olive | fullbleed | light | Fraunces serif |
| `realestate` | Cornerstone | premium property / architecture — slate + brass | split | light | Spectral serif |
| `fitness` | Ignite | high-energy gym / sport — dark, volt accent, condensed | fullbleed | dark | Oswald |
| `beauty` | Lumière | elegant salon / spa — blush + mauve | centered | light | Fraunces serif |
| `legal` | Sterling | authoritative law / advisory — navy + gold | split | light | Spectral serif |
| `creative` | Kinetic | bold studio / agency — near-black + acid accent | centered | light | Space Grotesk |
| `luxe` | Onyx | premium / luxury — near-black + gold, serif, airy | centered | dark | Fraunces serif |
| `education` | Scholar | school / tutoring — friendly blue + amber, rounded | split | light | Inter |
| `nonprofit` | Grove | cause / charity — warm green + amber, humane | centered | light | Inter |
| `finance` | Vault | finance / advisory — emerald + trust-blue, structured | split | light | Inter |
| `playful` | Pop | fun / kids / DTC — purple + pink + yellow, very rounded | centered | light | Space Grotesk |
| `neon` | Pulse | futuristic / gaming — near-black + cyan/magenta neon | fullbleed | dark | Space Grotesk |

**Industry shortcut:** `generate` with `{"industry":"<name>"}` (no preset) auto-maps common industries to the matching full template — e.g. `dental`/`clinic`/`wellness` → `healthcare`, `gym`/`yoga` → `fitness`, `cafe`/`bakery` → `restaurant`, `law`/`attorney` → `legal`, `saas`/`startup` → `tech`, `salon`/`spa` → `beauty`, `property`/`architecture` → `realestate`, `agency`/`studio`/`portfolio` → `creative`. Unmapped industries (education, accounting, retail, nonprofit, hospitality, construction) get a tuned palette over the default layout.

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
apple / notion / stripe → **minimal** · tesla / linear / vercel → **bold-dark** · airbnb → **editorial** · consultancy / SaaS-B2B → **corporate** · vercel-dashboard / dev tools → **tech** · clinic / dentist / wellness → **healthcare** · restaurant / café / bakery → **restaurant** · real estate / architecture → **realestate** · gym / fitness / sport → **fitness** · salon / spa / cosmetics → **beauty** · law firm / advisory → **legal** · studio / agency / portfolio → **creative**.

## 内容宽度（宽屏 · 窄屏 — 一句话即可调）

整站内容宽度就是一个 token：`tokens.layout.contentMaxWidth`（驱动页面容器 + 页脚的 `--layout-content-max`）。一条 PATCH **即时生效、无需重部署**。命名档位：

| 说法 | contentMaxWidth | 感觉 |
|---|---|---|
| 窄屏 / narrow | `1040px` | 聚焦、留白多，文字为主时好读 |
| 标准 / standard | `1160px` | 默认平衡 |
| 宽屏 / wide | `1280px` | 更充实，桌面铺得更开（**当前值**） |
| 全宽 / extra-wide | `1440px` | 大屏、几乎贴边 |

```bash
# “调宽一点 / make it wider / 宽屏”
curl -s -X PATCH "$ORACLE_SITE_API/admin/design" -H "Authorization: Bearer $ORACLE_SITE_TOKEN" -H "Content-Type: application/json" \
  -d '{"tokens":{"layout":{"contentMaxWidth":"1280px"}}}'
# 窄一点 → "1040px"；全宽 → "1440px"。其它布局 token 同理：sectionGap(段间距) · cardPadding · heroMinHeight · density。
```
> 换主题(`generate {preset}`)**默认保留当前宽度**——宽度是全局偏好,不会被主题重置。想换主题同时改宽度:`generate {"preset":"minimal","width":"wide"}`(width 接受 narrow/standard/wide/full 或具体 px)。

Hero 和长文本各自有可读上限（文字不会被拉太宽），这个 token 只管**整体页面容器**的宽度。

## Rules
- **Inspiration only — never clone a brand's exact identity or assets.**
- Keep it legible (contrast, spacing). Never hardcode styles in components — everything flows through this API → CSS variables.
- When the user is vague, propose options and confirm before applying a big visual change.
