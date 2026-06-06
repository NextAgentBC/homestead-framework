"""Runtime site identity — the single source of truth for the site's brand name,
industry, audience, region, and live-chat assistant name.

A ``SiteSettings`` singleton row (id=1) holds the live values; any blank field
falls back to the matching ``SITE_*`` config (the env defaults). This lets a
rebrand / "switch industry" change the whole site's identity — nav + footer
brand, blog lede, SEO description, and the chat persona — with **no redeploy**,
while a fresh deploy with no row still works straight from env.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from flask import current_app

from ..extensions import db
from ..models import DesignProfile, Page, SiteSettings
from . import block_service
from .design_service import profile_for_industry

# (settings attribute, config key) pairs — the config value is the fallback.
_FIELDS = (
    ("site_name", "SITE_NAME"),
    ("industry", "SITE_INDUSTRY"),
    ("audience", "SITE_AUDIENCE"),
    ("region", "SITE_REGION"),
    ("assistant_name", "SITE_ASSISTANT_NAME"),
)


def get_row() -> Optional[SiteSettings]:
    """The singleton settings row, or None if it has not been created yet."""
    return db.session.get(SiteSettings, 1)


def get_or_create_row() -> SiteSettings:
    """The singleton settings row, creating an empty one (id=1) if missing.
    Empty fields still resolve to env defaults via :func:`effective`."""
    row = db.session.get(SiteSettings, 1)
    if row is None:
        row = SiteSettings(id=1)
        db.session.add(row)
    return row


def effective() -> dict:
    """Effective site identity: DB row value where set, else the env default.
    ``assistant_name`` falls back to the brand name when blank, so the chat
    helper introduces itself as the site (per the configured default)."""
    cfg = current_app.config
    row = get_row()
    out: dict = {}
    for attr, key in _FIELDS:
        env_default = cfg.get(key, "") or ""
        value = (getattr(row, attr, "") or "").strip() if row else ""
        out[attr] = value or env_default
    if not (out.get("assistant_name") or "").strip():
        out["assistant_name"] = out.get("site_name") or ""
    return out


# Starter pages a fresh site gets (slug, page-template, nav order) so the nav is a
# real menu (Home · About · Services · Blog · Contact), not just two links. A
# rebrand rebuilds these same slugs from their templates for the new theme.
STARTER_PAGES = [("about", "about", 10), ("services", "services", 20)]
STARTER_SLUGS = {slug for slug, _tpl, _order in STARTER_PAGES}


def seed_demo(force: bool = False) -> list[str]:
    """Idempotently populate a fresh site so a new deploy is a real multi-page
    site, not a bare framework shell: a complete industry home (from SITE_INDUSTRY)
    plus starter pages. Returns the labels of what it created. Skips entirely once
    any design/page exists (unless ``force``), so existing data is never touched."""
    industry = current_app.config["SITE_INDUSTRY"]
    has_design = DesignProfile.query.first() is not None
    has_pages = Page.query.first() is not None
    if (has_design or has_pages) and not force:
        return []

    created: list[str] = []
    if not has_design:
        p = profile_for_industry(industry)
        db.session.add(DesignProfile(
            name=p["name"], status="active", source=p.get("source", "seed"),
            industry=p.get("industry", industry), personality=p.get("personality", ""),
            competitor_urls=p.get("competitorUrls", []), tokens=p["tokens"],
            voice=p["voice"], notes=p.get("notes", ""), sections=p.get("sections") or [],
        ))
        created.append(f"home design ({p['name']})")

    existing = {pg.slug for pg in Page.query.all()}
    for slug, template, order in STARTER_PAGES:
        if slug in existing:
            continue
        sections = block_service.build_page_template(template)
        meta = block_service.page_template(template)
        if not sections or not meta:
            continue
        title = meta["label"]
        page = Page(
            title=title, slug=slug, body_markdown="", sections=sections,
            status="published", nav_label=title, nav_order=order, show_in_nav=True,
            meta_title=title[:60], meta_description=(meta.get("blurb") or "")[:320],
            published_at=datetime.now(timezone.utc),
        )
        page.canonical_url = f"{current_app.config['SITE_URL']}/{page.slug}"
        db.session.add(page)
        created.append(f"page:{slug}")

    db.session.commit()
    return created
