# Site packs — export / import a reusable industry template

A **site pack** is a single `.tar.gz` that captures the *portable* parts of a
customized Homestead site — its active design (tokens, voice, home sections), all
pages, UI-chrome strings, and the media those reference — so a hand-tuned industry
sample can be re-applied to a fresh deploy in **minutes instead of hours**.

The workflow B2 is built around:

1. **Tune one sample really well** for an industry (e.g. a pressure-washing
   template): rebrand, edit the home + pages, upload real photos, translate.
2. **`flask site export`** it to a pack.
3. **Deploy a new client** the usual way (`ops/agent/deploy.sh`), then
   **`ops/agent/apply-site-pack.sh <pack> --rebrand-name "Client Co"`**.
4. **Set the client's NAP** (phone/email/address/hours). NAP never travels in a
   pack — the import ends by reminding you to do this.

The next client's site is then 90% done from your polished template; only the
contact identity and any bespoke copy remain.

---

## Two things that make a pack portable

### 1. Media URLs are domain-independent

Uploaded images are stored as **absolute** URLs
(`https://<API_PUBLIC_URL>/api/media/<file>`, the exact form the
`POST /api/admin/media` endpoint returns) inside `hero`/`gallery`/etc. block
content. That URL is bound to the source site's API domain, which would break on
a different deploy.

So a pack does not carry raw URLs:

- **Export** rewrites every `<scheme>://<host>/api/media/<file>` found in the
  design and page sections to a domain-less sentinel **`__MEDIA__/<file>`**, and
  copies the referenced file into the pack's `media/` directory.
- **Import** rewrites `__MEDIA__/<file>` back to
  `<api-base>/api/media/<file>` — where `--api-base` defaults to *this* site's
  `API_PUBLIC_URL` (the same base the upload endpoint uses) — and writes the
  bundled files back into `MEDIA_DIR`.

Result: the same pack works on any deploy, with images intact.

### 2. NAP never travels

The business's real-world **NAP** — legal name, phone, email, street/city/region/
postal/country, latitude/longitude, business hours, and the SiteSettings
service-areas list — is **deliberately excluded** from every pack. A pack is an
industry *template*, not a client identity. Copying one client's NAP into
another's site would:

- leak contact info between clients, and
- create the "**inconsistent NAP**" signal local search penalizes most (see the
  note on `SiteSettings` / `site_service.nap()`).

Only the generic identity — **site name, industry, audience, region** — is
exported. After importing, set the client's NAP via
`PATCH /api/admin/site/settings` (or a rebrand). Both `flask site import` and
`apply-site-pack.sh` print this reminder when they finish.

> A **page's** `local_business_overrides` (per-page city×service narrowing for
> JSON-LD, e.g. `{"service_areas": ["Surrey"]}`) *does* travel — that is template
> structure, not the business's contact NAP, and it lives on `Page`, not
> `SiteSettings`.

---

## Pack format

```
pack.tar.gz
├── manifest.json     # the whole site template (see below)
└── media/            # every media file the sections reference
    ├── hero-ab12cd34.png
    └── gallery-9f8e7d6c.jpg
```

`manifest.json`:

| key            | contents                                                                                                   |
| -------------- | ---------------------------------------------------------------------------------------------------------- |
| `schemaVersion`| pack format version (currently `1`; import refuses other versions)                                          |
| `exportedAt`   | ISO-8601 timestamp                                                                                          |
| `design`       | active `DesignProfile`: name/source/industry/personality/competitor_urls/tokens/voice/notes/sections/i18n  |
| `pages`        | every page: title/slug/body_markdown/status/nav_*/sections/meta_*/i18n/local_business_overrides (no ids/timestamps/canonical_url) |
| `uiMessages`   | UI-chrome strings per locale (only present if any exist)                                                    |
| `siteIdentity` | **generic identity only** — site_name/industry/audience/region (**no NAP**)                                 |
| `blog`         | published posts — **only** when exported with `--include-blog`                                              |
| `media`        | the list of media filenames the design + pages reference                                                    |

Media URLs inside `design` and `pages` are stored as the `__MEDIA__/<file>`
sentinel, not absolute URLs.

---

## CLI

### Export

```bash
flask --app app.main site export --out /path/to/pack.tar.gz [--include-blog]
```

- `--out` (required): destination `.tar.gz`.
- `--include-blog`: also bundle **published** blog posts (drafts are never
  exported). Omit it for a pure design/pages template.

If a referenced media file is missing from `MEDIA_DIR`, export warns and leaves it
out (the pack is still valid; that block will render a broken image until you
re-upload it on the target).

### Import

```bash
flask --app app.main site import /path/to/pack.tar.gz \
      [--rebrand-name "Client Co"] \
      [--api-base https://newapi.example.com] \
      [--force]
```

- `--rebrand-name`: override the pack's `site_name` for this client (other
  identity fields still come from the pack).
- `--api-base`: base URL for restored media links. **Default: this site's
  `API_PUBLIC_URL`** — the same base the media upload endpoint returns, so you
  normally don't need to pass it.
- `--force`: on a **page slug conflict**, overwrite the existing page from the
  pack. **Default behavior is skip + warn** — existing pages are never clobbered
  unless you ask. (Blog posts always skip on slug conflict.)

Import order: media files → design (overwrites/creates the active profile) →
pages → UI strings → generic identity → blog. Everything is committed in one
transaction.

Import intentionally **does not** touch NAP; it ends with:

```
import: NAP (phone/email/address/geo/hours) was NOT imported — set this
client's contact info via PATCH /api/admin/site/settings (or a rebrand).
```

---

## `ops/agent/apply-site-pack.sh` (Docker wrapper)

On a running instance the backend runs inside a container, so use the wrapper —
it `docker cp`s the pack into the backend container and runs `flask site import`
there, honoring `INSTANCE_NAME` (the compose project) exactly like `deploy.sh` /
`update.sh`.

```bash
bash ops/agent/apply-site-pack.sh <pack.tar.gz> \
     [--rebrand-name "Client Co"] [--api-base https://newapi.example.com] [--force]

# multi-instance host: target a named compose project
INSTANCE_NAME=acme bash ops/agent/apply-site-pack.sh ./acme-pack.tar.gz --rebrand-name "Acme"
```

The wrapper passes `--rebrand-name` / `--api-base` / `--force` straight through to
`flask site import`, and reminds you at the end to set the client's NAP.

---

## End-to-end example

```bash
# ── on the polished sample instance ──
flask --app app.main site export --out /tmp/pressure-washing.tar.gz
#   → copy /tmp/pressure-washing.tar.gz to the new host

# ── on a freshly deployed new instance ──
bash ops/agent/apply-site-pack.sh /tmp/pressure-washing.tar.gz --rebrand-name "Coastal Pressure Wash"

# ── finish: this client's real contact identity (NAP does NOT come from the pack) ──
curl -fsS -X PATCH "http://127.0.0.1:8000/api/admin/site/settings" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{
        "legalName": "Coastal Pressure Wash Ltd.",
        "phone": "+1-555-0142",
        "email": "hello@coastalpw.example.com",
        "addressStreet": "42 Marine Dr", "addressCity": "Surrey",
        "addressRegion": "BC", "addressPostalCode": "V3S 1A1", "addressCountry": "CA",
        "serviceAreas": ["Surrey", "Langley", "White Rock"]
      }'
```

The site is now the polished pressure-washing template, rebranded, with the new
client's own contact info — in minutes.
