import io
import json
import os
import re
import tarfile
from datetime import datetime, timedelta, timezone
from typing import Optional

import click
from flask import current_app
from flask.cli import AppGroup

from .auth import issue_jwt
from .extensions import db
from .models import BlogPost, DesignProfile, Page, SiteSettings, UiMessages, User
from .routes.admin import _create_post
from .services import site_service
from .services.ai_service import AIUnavailable, generate_blog_post

blog_cli = AppGroup("blog", help="Blog operations.")


@blog_cli.command("generate-daily")
@click.option("--topic", default=None)
@click.option("--draft", is_flag=True)
def generate_daily(topic: Optional[str], draft: bool):
    try:
        generated = generate_blog_post(topic)
    except AIUnavailable:
        # The daily timer keeps running; without a model there is simply no post today.
        click.echo("generate-daily: skipped, no AI model is configured (DEEPSEEK_API_KEY); nothing was published.")
        return
    publish = current_app.config["DAILY_BLOG_AUTOPUBLISH"] and not draft
    post = _create_post(generated, publish=publish)
    if not publish:
        post.status = "draft"
        post.published_at = None
        db.session.commit()
    click.echo(f"{post.status}: {post.title} ({post.slug}) at {datetime.now(timezone.utc).isoformat()}")


@click.group("token")
def token_cli():
    """Auth token operations (non-interactive)."""


@token_cli.command("issue")
@click.option("--email", default=None, help="Admin email (defaults to the first ADMIN_EMAILS entry).")
@click.option("--days", default=None, type=int, help="Token lifetime in days (default: JWT_EXPIRES_HOURS).")
def issue_token(email: Optional[str], days: Optional[int]):
    """Mint a bearer JWT for an admin user — for agents/CI, no browser needed."""
    admins = current_app.config["ADMIN_EMAILS"]
    if not email:
        if not admins:
            raise click.ClickException("ADMIN_EMAILS is empty; pass --email or set ADMIN_EMAILS.")
        email = sorted(admins)[0]
    email = email.strip().lower()
    if email not in admins:
        raise click.ClickException(
            f"{email!r} is not in ADMIN_EMAILS, so the token would not have admin access. "
            "Add it to ADMIN_EMAILS first."
        )
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email, google_sub=f"cli:{email}", name="CLI Admin", role="admin")
        db.session.add(user)
    else:
        user.role = "admin"
    db.session.commit()
    if days is not None:
        current_app.config["JWT_EXPIRES"] = timedelta(days=days)
    click.echo(issue_jwt(user))


@click.group("site")
def site_cli():
    """Site bootstrap / maintenance."""


@site_cli.command("seed")
@click.option("--force", is_flag=True, help="Add any missing starters even if some content already exists.")
def seed(force: bool):
    """Idempotently populate a fresh site so a new deploy is a real multi-page site,
    not a bare framework shell: a complete industry home (from SITE_INDUSTRY) plus
    starter pages. Skips once content exists (unless --force); existing data is never
    overwritten."""
    created = site_service.seed_demo(force=force)
    click.echo(f"seed: created {', '.join(created)}." if created
               else "seed: content already present — skipping.")


# --- Site packs: export/import a portable, brand-agnostic site template -------
#
# A site pack is a tar.gz of the *portable* parts of a customized site — the
# active design (tokens/voice/sections), all pages, UI strings, and the media
# they reference — so a hand-tuned industry sample can be re-applied to a fresh
# deploy in minutes instead of hours. Two things are deliberately made portable:
#   • Media URLs. Uploaded images are stored as ABSOLUTE URLs
#     (``<API_PUBLIC_URL>/api/media/<file>``) bound to the source domain. On
#     export every such URL in design/page sections is rewritten to a domain-less
#     sentinel ``__MEDIA__/<file>`` and the file copied into the pack; on import
#     the sentinel is rewritten to the *new* site's API base. So a pack is not
#     tied to the site it came from.
#   • NAP. The business's real-world contact identity (phone/email/address/geo/
#     hours/service areas/legal name) is NEVER exported — a pack is an industry
#     TEMPLATE, and copying one client's NAP into another's site would create the
#     "inconsistent NAP" local-search penalty (and leak contact info). Only the
#     generic identity (site_name/industry/audience/region) travels.

SITE_PACK_SCHEMA_VERSION = 1

# `<scheme>://<host>[:port]/api/media/<filename>` → captures the filename. The
# host part is greedy-free so it won't swallow across quotes/whitespace in JSON.
_MEDIA_URL_RE = re.compile(r"https?://[^\s\"']+?/api/media/([^\s\"'/?#]+)")
_MEDIA_SENTINEL = "__MEDIA__/"
# `__MEDIA__/<filename>` → captures the filename (for the import-side rewrite).
_MEDIA_SENTINEL_RE = re.compile(re.escape(_MEDIA_SENTINEL) + r"([^\s\"'/?#]+)")


def _to_media_sentinel(obj):
    """Deep-copy ``obj`` (JSON-ish: dict/list/str/scalars) rewriting every absolute
    ``.../api/media/<file>`` URL inside strings to ``__MEDIA__/<file>``. Returns
    the rewritten copy and the set of referenced media filenames."""
    seen: set[str] = set()

    def walk(node):
        if isinstance(node, str):
            def repl(m):
                seen.add(m.group(1))
                return _MEDIA_SENTINEL + m.group(1)
            return _MEDIA_URL_RE.sub(repl, node)
        if isinstance(node, list):
            return [walk(v) for v in node]
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        return node

    return walk(obj), seen


def _from_media_sentinel(obj, api_base: str):
    """Inverse of :func:`_to_media_sentinel`: rewrite ``__MEDIA__/<file>`` back to
    ``<api_base>/api/media/<file>`` throughout a JSON-ish structure."""
    prefix = f"{api_base.rstrip('/')}/api/media/"

    def walk(node):
        if isinstance(node, str):
            return _MEDIA_SENTINEL_RE.sub(lambda m: prefix + m.group(1), node)
        if isinstance(node, list):
            return [walk(v) for v in node]
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        return node

    return walk(obj)


def _active_design() -> Optional[DesignProfile]:
    return (DesignProfile.query.filter_by(status="active")
            .order_by(DesignProfile.updated_at.desc()).first())


def _build_pack_manifest(include_blog: bool, exported_at: Optional[datetime] = None):
    """Assemble the manifest dict + the set of referenced media filenames. Media
    URLs in design/page sections are rewritten to the ``__MEDIA__/`` sentinel."""
    media: set[str] = set()
    manifest: dict = {
        "schemaVersion": SITE_PACK_SCHEMA_VERSION,
        "exportedAt": (exported_at or datetime.now(timezone.utc)).isoformat(),
    }

    design = _active_design()
    if design is not None:
        sections, s = _to_media_sentinel(design.sections or [])
        media |= s
        i18n, s = _to_media_sentinel(design.i18n or {})
        media |= s
        manifest["design"] = {
            "name": design.name,
            "source": design.source,
            "industry": design.industry,
            "personality": design.personality,
            "competitor_urls": design.competitor_urls or [],
            "tokens": design.tokens or {},
            "voice": design.voice or {},
            "notes": design.notes,
            "sections": sections,
            "i18n": i18n,
        }

    pages = []
    for page in Page.query.order_by(Page.nav_order.asc(), Page.id.asc()).all():
        sections, s = _to_media_sentinel(page.sections or [])
        media |= s
        i18n, s = _to_media_sentinel(page.i18n or {})
        media |= s
        pages.append({
            "title": page.title,
            "slug": page.slug,
            "body_markdown": page.body_markdown,
            "status": page.status,
            "nav_label": page.nav_label,
            "nav_order": page.nav_order,
            "show_in_nav": page.show_in_nav,
            "sections": sections,
            "meta_title": page.meta_title,
            "meta_description": page.meta_description,
            "i18n": i18n,
            "local_business_overrides": page.local_business_overrides or {},
        })
    manifest["pages"] = pages

    ui = [row.to_dict() for row in UiMessages.query.order_by(UiMessages.locale.asc()).all()]
    if ui:
        manifest["uiMessages"] = ui

    # siteIdentity: generic identity ONLY. NAP (phone/email/address_*/legal_name/
    # geo/hours/service_areas) is deliberately excluded — see the module note.
    row = site_service.get_row()
    if row is not None:
        manifest["siteIdentity"] = {
            "site_name": row.site_name,
            "industry": row.industry,
            "audience": row.audience,
            "region": row.region,
        }

    if include_blog:
        blog = []
        for post in (BlogPost.query.filter_by(status="published")
                     .order_by(BlogPost.published_at.asc().nullslast(), BlogPost.id.asc()).all()):
            blog.append({
                "title": post.title,
                "slug": post.slug,
                "excerpt": post.excerpt,
                "body_markdown": post.body_markdown,
                "status": "published",
                "author": post.author,
                "tags": post.tags or [],
                "meta_title": post.meta_title,
                "meta_description": post.meta_description,
                "geo_region": post.geo_region,
                "i18n": post.i18n or {},
            })
        manifest["blog"] = blog

    manifest["media"] = sorted(media)
    return manifest, media


@site_cli.command("export")
@click.option("--out", "out_path", required=True, type=click.Path(dir_okay=False),
              help="Destination .tar.gz path for the site pack.")
@click.option("--include-blog", is_flag=True, help="Also include published blog posts.")
def site_export(out_path: str, include_blog: bool):
    """Export the active design + pages + UI strings + referenced media into a
    portable site pack (tar.gz). Media URLs are rewritten to the __MEDIA__/
    sentinel and the files bundled, so the pack is not tied to this domain. NAP
    contact info is NEVER exported (a pack is a template, not a client identity)."""
    manifest, media = _build_pack_manifest(include_blog)
    media_dir = current_app.config["MEDIA_DIR"]

    missing = []
    with tarfile.open(out_path, "w:gz") as tar:
        payload = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
        info = tarfile.TarInfo("manifest.json")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
        for name in sorted(media):
            src = os.path.join(media_dir, name)
            if os.path.isfile(src):
                tar.add(src, arcname=f"media/{name}")
            else:
                missing.append(name)

    click.echo(
        f"export: wrote {out_path} — design={'yes' if 'design' in manifest else 'no'}, "
        f"pages={len(manifest['pages'])}, media={len(media)}"
        f"{', blog=' + str(len(manifest['blog'])) if include_blog else ''}."
    )
    if missing:
        click.echo(f"export: WARNING — {len(missing)} referenced media file(s) not found "
                   f"in {media_dir} and left out of the pack: {', '.join(missing)}")


@site_cli.command("import")
@click.argument("pack_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--rebrand-name", default=None, help="Override the imported site_name (rebrand the pack for this client).")
@click.option("--api-base", default=None,
              help="Base URL for restored media links (default: this site's API_PUBLIC_URL).")
@click.option("--force", is_flag=True, help="Overwrite existing pages on slug conflict (default: skip + warn).")
def site_import(pack_path: str, rebrand_name: Optional[str], api_base: Optional[str], force: bool):
    """Import a site pack: restore media, design, pages, UI strings and generic
    site identity. The __MEDIA__/ sentinel is rewritten to --api-base (default:
    this site's API_PUBLIC_URL, the same base the media upload endpoint returns).
    NAP is NOT imported — set this client's contact info afterwards via
    PATCH /api/admin/site/settings (or a rebrand)."""
    base = (api_base or current_app.config["API_PUBLIC_URL"]).rstrip("/")
    media_dir = current_app.config["MEDIA_DIR"]

    with tarfile.open(pack_path, "r:gz") as tar:
        mf = tar.extractfile("manifest.json")
        if mf is None:
            raise click.ClickException("pack has no manifest.json — not a site pack.")
        manifest = json.loads(mf.read().decode("utf-8"))

        schema = manifest.get("schemaVersion")
        if schema != SITE_PACK_SCHEMA_VERSION:
            raise click.ClickException(
                f"unsupported pack schemaVersion {schema!r} (this build imports {SITE_PACK_SCHEMA_VERSION}).")

        # 1) media: write bundled files back into MEDIA_DIR (skip if present).
        os.makedirs(media_dir, exist_ok=True)
        wrote_media = skipped_media = 0
        for member in tar.getmembers():
            if not member.isfile() or not member.name.startswith("media/"):
                continue
            name = os.path.basename(member.name)
            if not name:
                continue
            dest = os.path.join(media_dir, name)
            if os.path.exists(dest):
                skipped_media += 1
                continue
            src = tar.extractfile(member)
            if src is None:
                continue
            with open(dest, "wb") as fh:
                fh.write(src.read())
            wrote_media += 1

    # 2) design: overwrite the active profile, or create one if none exists.
    created_labels: list[str] = []
    if manifest.get("design"):
        d = _from_media_sentinel(manifest["design"], base)
        profile = _active_design()
        if profile is None:
            profile = DesignProfile(status="active")
            db.session.add(profile)
        profile.name = d.get("name", "") or ""
        profile.status = "active"
        profile.source = d.get("source", "site-pack") or "site-pack"
        profile.industry = d.get("industry", "") or ""
        profile.personality = d.get("personality", "") or ""
        profile.competitor_urls = d.get("competitor_urls", []) or []
        profile.tokens = d.get("tokens", {}) or {}
        profile.voice = d.get("voice", {}) or {}
        profile.notes = d.get("notes", "") or ""
        profile.sections = d.get("sections", []) or []
        profile.i18n = d.get("i18n", {}) or {}
        created_labels.append("design")

    # 3) pages: create; on slug conflict skip+warn (or overwrite with --force).
    page_new = page_skipped = page_overwritten = 0
    for raw in manifest.get("pages", []):
        p = _from_media_sentinel(raw, base)
        slug = p.get("slug")
        if not slug:
            continue
        existing = Page.query.filter_by(slug=slug).first()
        if existing is not None and not force:
            page_skipped += 1
            click.echo(f"import: page '{slug}' already exists — skipping (use --force to overwrite).")
            continue
        page = existing or Page(slug=slug)
        if existing is None:
            db.session.add(page)
            page_new += 1
        else:
            page_overwritten += 1
        page.title = p.get("title", "") or ""
        page.body_markdown = p.get("body_markdown", "") or ""
        page.status = p.get("status", "draft") or "draft"
        page.nav_label = p.get("nav_label", "") or ""
        page.nav_order = int(p.get("nav_order", 100) or 100)
        page.show_in_nav = bool(p.get("show_in_nav", True))
        page.sections = p.get("sections", []) or []
        page.meta_title = p.get("meta_title", "") or ""
        page.meta_description = p.get("meta_description", "") or ""
        page.i18n = p.get("i18n", {}) or {}
        page.local_business_overrides = p.get("local_business_overrides", {}) or {}
        page.canonical_url = f"{current_app.config['SITE_URL']}/{slug}"
        if page.status == "published" and not page.published_at:
            page.published_at = datetime.now(timezone.utc)

    # 4) uiMessages: upsert per locale.
    ui_count = 0
    for entry in manifest.get("uiMessages", []):
        loc = (entry.get("locale") or "").strip().lower()
        if not loc:
            continue
        row = UiMessages.query.filter_by(locale=loc).first()
        if row is None:
            row = UiMessages(locale=loc, messages={})
            db.session.add(row)
        row.messages = entry.get("messages") or {}
        ui_count += 1

    # 5) siteIdentity: generic identity only (NAP is intentionally NOT imported).
    identity = manifest.get("siteIdentity") or {}
    if identity or rebrand_name:
        row = site_service.get_or_create_row()
        for attr in ("site_name", "industry", "audience", "region"):
            if attr in identity and isinstance(identity[attr], str):
                setattr(row, attr, identity[attr])
        if rebrand_name:
            row.site_name = rebrand_name

    # 6) blog (only present when the pack was exported with --include-blog).
    blog_new = blog_skipped = 0
    for raw in manifest.get("blog", []):
        p = _from_media_sentinel(raw, base)
        slug = p.get("slug")
        if not slug:
            continue
        if BlogPost.query.filter_by(slug=slug).first() is not None:
            blog_skipped += 1
            continue
        post = BlogPost(
            title=p.get("title", "") or "", slug=slug, excerpt=p.get("excerpt", "") or "",
            body_markdown=p.get("body_markdown", "") or "", status="published",
            author=p.get("author", "Editorial") or "Editorial", tags=p.get("tags", []) or [],
            meta_title=p.get("meta_title", "") or "", meta_description=p.get("meta_description", "") or "",
            geo_region=p.get("geo_region", "") or "", i18n=p.get("i18n", {}) or {},
            published_at=datetime.now(timezone.utc),
        )
        post.canonical_url = f"{current_app.config['SITE_URL']}/blog/{slug}"
        db.session.add(post)
        blog_new += 1

    db.session.commit()

    click.echo(
        f"import: media(+{wrote_media}, skipped {skipped_media}), "
        f"design={'yes' if 'design' in created_labels else 'no'}, "
        f"pages(+{page_new}, overwritten {page_overwritten}, skipped {page_skipped}), "
        f"uiMessages={ui_count}"
        + (f", blog(+{blog_new}, skipped {blog_skipped})" if "blog" in manifest else "")
        + f". media links → {base}/api/media/…"
    )
    click.echo("import: NAP (phone/email/address/geo/hours) was NOT imported — set this "
               "client's contact info via PATCH /api/admin/site/settings (or a rebrand).")
