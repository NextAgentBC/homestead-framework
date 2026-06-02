# Homestead

> **Homestead** — an "Elementor, but driven entirely by chat (OpenClaw/Codex)" website framework.
> Everything is **design tokens + composable blocks**, with zero hard-coded CSS.
> (Internal identifiers — repo dirs, services, the `oracle-site` DB, the `oracle-site-*` skills — keep the original `oracle-site` codename; only the product name is Homestead.)
> Categorized capability map (APIs · fonts · 18 themes · 15 blocks · skills): [`docs/REFERENCE.zh.md`](docs/REFERENCE.zh.md).

> 🤖 **Deploying with an AI agent?** Hand it **[`AGENT-DEPLOY.md`](AGENT-DEPLOY.md)** — a headless,
> idempotent, self-verifying runbook: clone → env → build → Cloudflare tunnel **via API** → verify.
> No dashboard. The human provides a server + domain + a Cloudflare API token; the agent does the rest.

This README is written for a student's local Codex agent.

Canonical repository:

```text
https://github.com/NextAgentBC/homestead-framework
```

Your human is taking a lecture where every student has:

- A local computer with Codex installed.
- SSH access to an Oracle VM through the alias `oracle-server`.
- OpenClaw installed on the Oracle VM.
- A DeepSeek API key.
- Google Workspace CLI / GWS access.
- A Cloudflare-managed domain or subdomain.

Your job is to reproduce, deploy, and maintain this framework for that student.

## Before The Lecture

Each student completes [`docs/student-prep.md`](docs/student-prep.md) first — a beginner-friendly walkthrough (in Chinese) of the account, domain, Google OAuth, and credential setup the list above assumes. Steps are marked 🤖 (Codex can run/verify) or 🧑 (human, browser-only).

## Goal

Build a reusable full-stack website framework:

- Frontend: Next.js.
- Backend: Python Flask API.
- Database: PostgreSQL.
- Auth: Google Sign-In.
- Content: blog + newsletter + standalone pages.
- Composition: every page (and the home) is an ordered list of **blocks** (15 types) edited by API — add/move/edit/remove/duplicate, instant, no redeploy.
- Theming: **18 one-shot style presets** (base + industry + style), all token-driven; switch with one call.
- Media: **upload-only** image hosting used by gallery/team/blog (`/api/admin/media`).
- i18n: path-based `/zh`, the agent is the translator.
- Capture: rebuild a section from a screenshot into the flexible `section` block + a reusable pattern library.
- UI/UX: API-driven design profile, not hard-coded theme values.
- Live chat: a floating widget answered by a **sandboxed, tool-less 小爪** (via the host `webchat-bridge`), each exchange mirrored to the operator's Telegram, with human take-over. Setup: [`docs/deploy-new-instance.md`](docs/deploy-new-instance.md) §8 · [`ops/webchat-bridge/`](ops/webchat-bridge/README.md).
- Automation: daily AI-generated blog posts.
- Delivery: Cloudflare Tunnel preferred, static IP + Nginx fallback.
- Maintenance: OpenAPI contract and clear module boundaries for OpenClaw/Codex.

The industry/theme is intentionally not fixed. Treat the theme as configuration.

## Repository Layout

```text
frontend/   Next.js App Router website
backend/    Flask API, SQLAlchemy models, auth, AI blog generator, email service
docs/       API, deployment, lecture, and maintenance notes
ops/        systemd, nginx, and cloudflared examples
```

Important backend files:

- `backend/app/models.py`: database source of truth.
- `backend/app/routes/`: HTTP API behavior.
- `backend/app/services/`: replaceable integrations such as DeepSeek and SMTP.
- `backend/app/openapi.json`: machine-readable API map for OpenClaw/Codex.
- `backend/app/services/design_service.py`: industry design presets and token merge logic.
- `backend/app/services/competitor_analyzer.py`: public competitor signal extraction for UI/UX profiles.
- `backend/migrations/`: Alembic/Flask-Migrate migrations.

Important frontend files:

- `frontend/app/page.tsx`: first screen.
- `frontend/app/blog/`: blog index and detail pages.
- `frontend/components/google-login.tsx`: Google Sign-In integration.
- `frontend/components/newsletter-form.tsx`: newsletter signup.
- `frontend/lib/api.ts`: all frontend API calls.
- `frontend/lib/design.ts`: maps API design tokens to CSS variables.

## Local Development

Use PostgreSQL. SQLite is only a fallback for quick experiments.

1. Install dependencies:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
```

2. Create env files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

3. Start PostgreSQL.

Preferred:

```bash
docker compose up -d postgres
```

If Docker Compose is not available but Docker itself works:

```bash
docker run -d --name oracle-site-postgres \
  -e POSTGRES_DB=oracle_site \
  -e POSTGRES_USER=oracle_site \
  -e POSTGRES_PASSWORD=oracle_site_password \
  -p 127.0.0.1:5432:5432 \
  postgres:17-alpine
```

If Docker is not running locally, use an existing PostgreSQL server and set `DATABASE_URL` in `backend/.env`.

4. Run migrations:

```bash
cd backend
. .venv/bin/activate
flask --app app.main db upgrade
```

5. Start backend and frontend:

```bash
cd backend
. .venv/bin/activate
flask --app app.main run --port 8000
```

```bash
cd frontend
npm run dev -- --port 3000
```

6. Verify:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/openapi.json
curl http://localhost:3000
```

## Required Environment Variables

Backend:

```text
SECRET_KEY=
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:55433/DB
CORS_ORIGINS=https://student-domain.example
SITE_NAME=
SITE_URL=https://student-domain.example
API_PUBLIC_URL=https://api.student-domain.example
SITE_INDUSTRY=
SITE_AUDIENCE=
SITE_REGION=
GOOGLE_CLIENT_ID=
ADMIN_EMAILS=
DEEPSEEK_API_KEY=
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_FROM=
```

Frontend:

```text
NEXT_PUBLIC_API_BASE_URL=https://api.student-domain.example/api
NEXT_PUBLIC_SITE_URL=https://student-domain.example
NEXT_PUBLIC_GOOGLE_CLIENT_ID=
```

## API Contract

Machine-readable source of truth: `GET /api/openapi.json`. A categorized human map
(APIs · fonts · 18 themes · 15 blocks · skill↔API) lives in [`docs/REFERENCE.zh.md`](docs/REFERENCE.zh.md).

Public (no token):

- `GET /api/health` · `GET /api/site` · `GET /api/design` (`?locale=`) · `GET /api/openapi.json`
- `GET /api/blocks` — block catalog (types, variants, fields, icons)
- `GET /api/patterns` · `GET /api/patterns/:slug` — saved section patterns
- `GET /api/i18n/:locale` — UI chrome strings · `GET /api/media/:filename` — self-hosted images
- `GET /api/blogs` (`?locale=`) · `GET /api/blogs/:slug`
- `GET /api/pages` (`?locale=`) · `GET /api/pages/:slug`
- `POST /api/auth/google` · `POST /api/newsletter/subscribe` · `POST /api/contact`

Admin (`Authorization: Bearer <jwt>`):

- **Design** — `GET|PATCH /api/admin/design` · `POST /api/admin/design/generate` · `POST /api/admin/design/analyze-competitors`
- **Blogs** — `POST /api/admin/blogs` · `PATCH /api/admin/blogs/:id` · `POST /api/admin/blogs/generate`
- **Pages** — `POST /api/admin/pages` · `PATCH|DELETE /api/admin/pages/:id`
- **Compose** (block-level page editing) — `GET /api/admin/surfaces` · `GET|POST /api/admin/compose/:target/blocks` · `PATCH|DELETE …/blocks/:id` · `POST …/blocks/:id/move` · `…/duplicate` · `POST /api/admin/compose/:target/batch`
- **Patterns** — `POST /api/admin/patterns` · `DELETE /api/admin/patterns/:id`
- **i18n** — `PATCH /api/admin/i18n/:locale`
- **Media** (upload-only) — `GET|POST /api/admin/media` · `DELETE /api/admin/media/:filename`

Get a non-interactive admin token (runs where the backend runs):

```bash
flask --app app.main token issue --email you@example.com
```

## UI/UX Personalization

Do not make every student website look the same.

The frontend consumes `GET /api/design`, then maps the returned tokens to CSS variables. Do not hard-code permanent colors, fonts, radii, or layout density inside page components unless they are structural and industry-neutral.

Design profile responsibilities:

- `industry`: education, accounting, retail, healthcare, real estate, etc.
- `competitorUrls`: websites the student's Codex/OpenClaw should inspect for design direction.
- `tokens.colors`: brand palette and contrast system. Includes `surfaceInverse` / `inkInverse` (the dark "contrast band" behind a full-bleed hero and the CTA banner) and `onPrimary` (text/icon color on primary-filled buttons) so even the dark surfaces are theme-driven, never hard-coded in components.
- `tokens.typography`: body, heading, and monospace font stacks.
- `tokens.radius`: card/control/pill shape.
- `tokens.layout`: max content width, hero height, spacing density.
- `voice`: headline and tone guidance for page copy.
- `notes`: rationale so future agents know why the design exists.

Generate a profile:

```bash
curl -X POST https://api.student-domain.example/api/admin/design/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "accounting",
    "competitorUrls": [
      "https://example-accounting-firm.com",
      "https://another-local-competitor.com"
    ],
    "notes": "Use competitor URLs as visual references, but create a distinct identity."
  }'
```

Update one design token:

```bash
curl -X PATCH https://api.student-domain.example/api/admin/design \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tokens": {
      "colors": {
        "primary": "#174f7a",
        "accent": "#b85c38"
      }
    }
  }'
```

When using competitor sites, never copy a competitor's exact brand identity. Use them to infer category expectations, spacing density, visual hierarchy, and content patterns, then produce a distinct profile.

Analyze competitor websites:

```bash
curl -X POST https://api.student-domain.example/api/admin/design/analyze-competitors \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "retail",
    "competitorUrls": [
      "https://example-retailer.com",
      "https://another-local-shop.com"
    ],
    "observations": [
      {
        "url": "https://example-retailer.com",
        "colors": ["#a6422b", "#28666e"],
        "fonts": ["Nunito Sans"],
        "layoutNotes": "Warm product-forward homepage with clear sale CTAs."
      }
    ],
    "notes": "Use category conventions, but create a distinct identity."
  }'
```

OpenClaw browser workflow lives in `docs/openclaw-competitor-analyzer.md`.

## Internationalization & screenshot capture

Two agent-driven capabilities; architecture in [`docs/capture-and-i18n.md`](docs/capture-and-i18n.md).

- **i18n (path-based `/zh`)** — content is never single-language. Each entity carries an
  `i18n` map; OpenClaw/Codex *is* the translator (it reads the English blocks and writes the
  Chinese ones). Set `SITE_LOCALES` / `SITE_DEFAULT_LOCALE` (and the frontend's
  `NEXT_PUBLIC_SITE_LOCALES`). Read localized content with `?locale=zh` on `/api/design`,
  `/api/pages*`, `/api/blogs*`; write with `?locale=zh` on the admin routes. UI chrome strings:
  `GET /api/i18n/:locale`, `PATCH /api/admin/i18n/:locale`. Skill: `oracle-site-i18n`.
- **Capture** — rebuild a section from a screenshot into the flexible, token-driven `section`
  block (so it auto-harmonizes to the theme — inspiration, never a pixel copy). Save good ones
  to the pattern library (`GET /api/patterns`, `POST /api/admin/patterns`) to grow the block
  vocabulary with no redeploy. Skill: `oracle-site-capture`.

## Daily Blog Automation

Generate and publish:

```bash
cd backend
. .venv/bin/activate
flask --app app.main blog generate-daily
```

Generate draft:

```bash
flask --app app.main blog generate-daily --draft
```

If `DEEPSEEK_API_KEY` is not set, the command creates a deterministic fallback post so deployment can still be tested.

## Deploy To Oracle Server

The expected SSH alias is:

```bash
ssh oracle-server
```

Recommended server path:

```text
/home/ubuntu/projects/oracle-site
```

Recommended deployment steps:

```bash
ssh oracle-server 'mkdir -p ~/projects/oracle-site'
rsync -av --exclude node_modules --exclude .next --exclude .venv ./ oracle-server:~/projects/oracle-site/
ssh oracle-server 'cd ~/projects/oracle-site && cp backend/.env.example backend/.env && cp frontend/.env.example frontend/.env.local'
```

Then edit env files on the server. After env files are ready:

```bash
ssh oracle-server 'cd ~/projects/oracle-site && docker compose up -d --build'
ssh oracle-server 'cd ~/projects/oracle-site && docker compose ps'
ssh oracle-server 'curl -fsS http://127.0.0.1:8000/api/health'
```

## Cloudflare Decision

Use Cloudflare Tunnel first.

Reason:

- No need to expose Oracle VM ports 80/443.
- TLS is handled at Cloudflare.
- Origin IP is less exposed.
- Students get the same repeatable deployment pattern.

Expected routing:

```text
student-domain.example      -> frontend:3000
api.student-domain.example  -> backend:8000
```

If the server already has an `infra` Cloudflare Tunnel, add ingress routes there instead of creating a second tunnel.

## OpenClaw Maintenance Instructions

When OpenClaw or Codex modifies this project:

1. Respect the API contract in `docs/api-contract.md`.
2. Keep database changes in `backend/app/models.py` plus a migration.
3. Keep integrations isolated in `backend/app/services/`.
4. Keep UI/UX personalization in the design profile API and CSS variables.
5. Never hard-code API keys, SMTP passwords, OAuth secrets, or Cloudflare tokens.
6. Preserve `/api/openapi.json`.
7. Run these checks before reporting success:

```bash
cd backend
. .venv/bin/activate
pytest -q
flask --app app.main db upgrade
flask --app app.main routes
flask --app app.main blog generate-daily --draft

cd ../frontend
npm run typecheck
npm run build
```

7. Verify live services:

```bash
curl -fsS http://127.0.0.1:8000/api/health
curl -fsS http://127.0.0.1:8000/api/openapi.json
curl -fsS http://127.0.0.1:3000
```

## Teaching Model

Explain the system as four layers:

1. Domain layer: Cloudflare owns public DNS, TLS, and routing.
2. App layer: Next.js handles pages, metadata, sitemap, and user experience.
3. Capability layer: Flask owns identity, users, blog records, newsletter records, email, and AI jobs.
4. Agent layer: Codex/OpenClaw maintain the project through API contracts, env files, migrations, and deployment scripts.

The point of the lecture is not one website. The point is a repeatable personal-server operating system for building websites.
