<div align="center">

# Homestead

**Professional websites for local businesses — deployed in minutes, managed by chat.**

Pick an industry, point it at a domain, hand the owner a Telegram bot. That's the whole product.

[中文](README.zh.md) · [Deploy it (AI agent)](AGENT-DEPLOY.md) · [Capability map](docs/REFERENCE.zh.md) · [Developer docs](docs/DEVELOPMENT.md) · [License: AGPL-3.0](LICENSE)

</div>

---

## What this is

Homestead is a full-stack website framework (**Next.js + Flask + PostgreSQL**) built to be **produced in bulk and run from a phone**. It's "Elementor, but driven entirely by chat" — every page is design **tokens + composable blocks** with zero hard-coded CSS, and everything (design, content, translation, media, live-chat takeover) is editable through an API or a **Telegram bot**. No dashboard, no page builder, no code.

It exists to make one business model cheap and repeatable: **sell a real, professional website to a local business for ~$100**, then deliver and maintain it at near-zero marginal cost. Three things make that work:

| Advantage | How Homestead delivers it |
|---|---|
| **1. Bulk production** | One command deploys a fully independent instance (own DB, domain, content). `docker compose` + `ops/agent/deploy.sh` + a Cloudflare tunnel over API. Many client sites coexist on one host — see [`docs/multi-instance.md`](docs/multi-instance.md). |
| **2. Deep industry fit** | A dozen **complete, image-ready industry templates** (9 blocks + declared imagery each). One call — `POST /api/admin/site/rebrand` — reskins the entire site to a new industry, then `GET /api/admin/consistency` machine-verifies nothing was left half-done. |
| **3. AI-driven, mobile-first management** | The owner (or you, on their behalf) changes the whole site by **texting a Telegram bot** in plain language — "make my site a pest-control company", "put this photo on the homepage", "translate everything to Chinese", "a customer is asking about pricing, reply for me". Undo any change with a sentence. This is what Wix and WordPress can't do. |

Everything runs on **your** server and domain. Content and audience belong to the client.

---

## Industry templates

A dozen industries ship as **complete, image-ready homepages** — full-bleed photo hero → services → gallery → process → pricing → FAQ → CTA, with every image slot pre-labelled so a fresh site looks finished before a single photo is uploaded. Switch between them with one `rebrand` call; add a new one with a single spec entry.

| | | |
|---|---|---|
| **Home services / trades** `construction` <br/> _pressure washing · plumbing · electrical · HVAC · landscaping · roofing · pest control · junk removal…_ | **Beauty & spa** `beauty` <br/> ![beauty](frontend/public/demo/beauty-hero.jpg) | **Restaurant & café** `restaurant` <br/> ![restaurant](frontend/public/demo/restaurant-hero.jpg) |
| **Healthcare & clinics** `healthcare` <br/> ![healthcare](frontend/public/demo/healthcare-hero.jpg) | **Legal & advisory** `legal` <br/> ![legal](frontend/public/demo/legal-hero.jpg) | **Fitness & gym** `fitness` <br/> ![fitness](frontend/public/demo/fitness-hero.jpg) |
| **Real estate** `realestate` <br/> ![realestate](frontend/public/demo/realestate-hero.jpg) | **Creative / agency** `creative` <br/> ![creative](frontend/public/demo/creative-hero.jpg) | **Tech / SaaS** `tech` <br/> ![tech](frontend/public/demo/tech-hero.jpg) |
| **Education & tutoring** `education` <br/> ![education](frontend/public/demo/education-hero.jpg) | **Finance & advisory** `finance` <br/> ![finance](frontend/public/demo/finance-hero.jpg) | **Nonprofit** `nonprofit` <br/> ![nonprofit](frontend/public/demo/nonprofit-hero.jpg) |

Plus token-only presets (`minimal`, `bold-dark`, `editorial`, `corporate`, `luxe`, `neon`, `playful`, …) for a distinct look on top of any structure — **19 style presets** in total. Full catalog (fonts · themes · 15 block types · skills ↔ API): [`docs/REFERENCE.zh.md`](docs/REFERENCE.zh.md).

> **Try it live:** with `SITE_DEMO_PREVIEW=true`, a visitor can preview the whole site as any industry from the chat widget — a live, self-serve template gallery.

---

## Built-in SEO / GEO / AEO

Local businesses get found through Google **and** AI answer engines. Every Homestead site ships with the technical layer competitors usually skip:

- **Structured data (JSON-LD):** `LocalBusiness` + `Service` + `FAQPage` + `BreadcrumbList`, driven by the site's real NAP (name, address, phone, hours, service areas). No `AggregateRating`/`Review` markup — Google disqualifies self-hosted review stars, so it's deliberately omitted.
- **NAP consistency** as a first-class data model (`SiteSettings` + per-page `local_business_overrides` for city-specific landing pages).
- **`sitemap.xml`** covering every page, **`robots.txt`**, and **`/llms.txt`**.
- **Server-rendered HTML** so AI crawlers (GPTBot, ClaudeBot, PerplexityBot — none execute JavaScript) read full content.

---

## Deploy in minutes

You provide a server, a domain on Cloudflare, and a Cloudflare API token. The agent does the rest.

```bash
git clone https://github.com/NextAgentBC/homestead-framework.git homestead && cd homestead

export SITE_DOMAIN=client.example.com API_DOMAIN=client-api.example.com \
       ADMIN_EMAIL=you@example.com CF_API_TOKEN=… CF_ACCOUNT_ID=…
export SITE_INDUSTRY=construction          # any industry key above
bash ops/agent/deploy.sh                    # env → build → health → token → tunnel → verify
```

`deploy.sh` is idempotent and self-verifying — re-run it after fixing anything it reports. On first boot the site is already a complete, multi-page demo in the chosen industry. Then customize by chat or API, and hand the owner their bot.

- **Sign → deliver checklist (how the $100 gets earned):** [`docs/runbook-client-delivery.md`](docs/runbook-client-delivery.md) — timed, step-by-step, with an acceptance gate
- **Full headless runbook (for an AI agent):** [`AGENT-DEPLOY.md`](AGENT-DEPLOY.md)
- **Make a deployed site the client's:** [`docs/getting-started.zh.md`](docs/getting-started.zh.md) — rebrand → swap photos → edit copy → translate → consistency check
- **Many clients on one host:** [`docs/multi-instance.md`](docs/multi-instance.md)
- **Update a live site:** `bash ops/agent/update.sh`

All docs, indexed by who you are (buyer / owner / operator / developer): [`docs/README.md`](docs/README.md).

---

## Manage it from your phone

Once deployed, the site is driven by an OpenClaw agent exposed as a **Telegram bot**. Real messages the owner (or operator) can send:

> "Change my site to a plumbing company called Rapid Rooter" → whole site reskins, brand + copy updated
> "Put this photo on the homepage" _(attach a picture)_ → uploaded and live in seconds
> "Add a blog post about spring gutter cleaning" · "Translate the site to Chinese" · "Undo that"
> _(a visitor asks a question on the site)_ → mirrored to your Telegram; reply once to take over the chat

Each block type also has its own lightweight skill (`add an FAQ`, `add a pricing table`, …) that routes to the composition engine. The chat brain is **sandboxed and tool-less** — it can't touch the server, only the public site's content.

Set this up from scratch (OpenClaw + Telegram bot, and the three delivery models — operator-managed / shared / per-client): [`docs/telegram-agent-setup.md`](docs/telegram-agent-setup.md). Hand the owner a plain-language guide: [`docs/owner-manual.zh.md`](docs/owner-manual.zh.md) · the site's built-in AI live chat, for owners: [`docs/webchat-for-owners.zh.md`](docs/webchat-for-owners.zh.md).

Skills ↔ API map: [`skills/README.md`](skills/README.md) · [`docs/REFERENCE.zh.md`](docs/REFERENCE.zh.md).

---

## Under the hood

- **Frontend** — Next.js App Router, server-rendered, token-driven theming (no hard-coded industry styling).
- **Backend** — Flask + SQLAlchemy + PostgreSQL; small, stable, documented API (`backend/app/openapi.json`).
- **Content model** — pages and the home are ordered lists of typed **blocks** (15 types); design lives in a separate token profile, so structure and skin stay decoupled.
- **Ops** — `docker-compose` (parameterized for multi-instance), Cloudflare tunnel over API, self-hosted media, daily AI blog automation.

Architecture, local development, environment variables, API contract, and maintenance notes live in [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

---

## License

[AGPL-3.0](LICENSE). You can deploy Homestead for clients and charge for it. If you offer it to others as a hosted service, the license requires you to make your modifications available under the same terms.

<sub>Internal identifiers (repo dirs, services, the `homestead-site` database, the `homestead-site-*` skills) keep the original `homestead-site` codename; only the product name is Homestead.</sub>
