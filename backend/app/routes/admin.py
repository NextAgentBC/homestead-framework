import base64
import os
import secrets
import urllib.parse
import urllib.request
from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional

from flask import Blueprint, current_app, jsonify, request
from slugify import slugify
from werkzeug.utils import secure_filename

from ..auth import require_auth
from ..extensions import db
from ..models import BlockPattern, BlogPost, DesignProfile, Page, UiMessages
from ..services.ai_service import generate_blog_post
from ..services.competitor_analyzer import analyze_competitors
from ..services.design_service import apply_style, deep_merge, normalized_profile, profile_for_industry
from ..services import block_service

bp = Blueprint("admin", __name__)


def _admin_locale():
    """Validated ?locale= for write endpoints. None means the default locale
    (edit the base columns); a non-default locale edits the i18n[locale] map."""
    loc = (request.args.get("locale") or "").strip().lower()
    if not loc or loc == current_app.config["SITE_DEFAULT_LOCALE"]:
        return None
    if loc not in current_app.config["SITE_LOCALES"]:
        return None
    return loc


def _set_i18n(obj, locale: str, fields: dict):
    """Merge localized field overrides into obj.i18n[locale] (reassign the JSON
    column so SQLAlchemy persists it)."""
    data = dict(obj.i18n or {})
    entry = dict(data.get(locale) or {})
    entry.update({k: v for k, v in fields.items() if v is not None})
    data[locale] = entry
    obj.i18n = data


def _active_design_profile() -> Optional[DesignProfile]:
    return DesignProfile.query.filter_by(status="active").order_by(DesignProfile.updated_at.desc()).first()


def _unique_slug(slug: str, model=BlogPost) -> str:
    base = slugify(slug) or "post"
    candidate = base
    index = 2
    while model.query.filter_by(slug=candidate).first():
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def _create_post(data: dict, publish: bool) -> BlogPost:
    status = "published" if publish else data.get("status", "draft")
    post = BlogPost(
        title=data["title"],
        slug=_unique_slug(data.get("slug") or data["title"]),
        excerpt=data.get("excerpt", ""),
        body_markdown=data["body_markdown"],
        status=status,
        tags=data.get("tags", []),
        meta_title=data.get("meta_title", data["title"][:60]),
        meta_description=data.get("meta_description", data.get("excerpt", ""))[:320],
        geo_region=data.get("geo_region", current_app.config["SITE_REGION"]),
        published_at=datetime.now(timezone.utc) if status == "published" else None,
    )
    post.canonical_url = f"{current_app.config['SITE_URL']}/blog/{post.slug}"
    db.session.add(post)
    db.session.commit()
    return post


@bp.post("/blogs/generate")
@require_auth(admin=True)
def generate_blog():
    data = request.get_json(silent=True) or {}
    generated = generate_blog_post(data.get("topic"))
    post = _create_post(generated, publish=bool(data.get("publish", False)))
    return {"item": post.to_detail_dict()}


@bp.post("/blogs")
@require_auth(admin=True)
def create_blog():
    data = request.get_json(silent=True) or {}
    if not data.get("title") or not data.get("body_markdown"):
        return jsonify({"error": {"code": "bad_request", "message": "title and body_markdown are required"}}), 400
    post = _create_post(data, publish=data.get("status") == "published")
    return {"item": post.to_detail_dict()}, 201


@bp.patch("/blogs/<int:post_id>")
@require_auth(admin=True)
def update_blog(post_id: int):
    post = db.session.get(BlogPost, post_id)
    if not post:
        return jsonify({"error": {"code": "not_found", "message": "Blog post not found"}}), 404
    data = request.get_json(silent=True) or {}
    locale = _admin_locale()
    if locale:
        # Translation: localizable fields go into i18n[locale]; status/published stay global.
        _set_i18n(post, locale, {k: data[k] for k in
                  ["title", "excerpt", "body_markdown", "tags", "meta_title", "meta_description"] if k in data})
    else:
        for key in ["title", "excerpt", "body_markdown", "tags", "meta_title", "meta_description", "geo_region"]:
            if key in data:
                setattr(post, key, data[key])
    if "status" in data:
        post.status = data["status"]
    if data.get("status") == "published" and not post.published_at:
        post.published_at = datetime.now(timezone.utc)
    db.session.commit()
    return {"item": post.to_detail_dict(locale)}


@bp.get("/design")
@require_auth(admin=True)
def get_design():
    locale = _admin_locale()
    profile = _active_design_profile()
    if not profile:
        data = profile_for_industry(current_app.config["SITE_INDUSTRY"])
        return {"item": data}
    return {"item": normalized_profile(profile.to_dict(locale), profile.industry or current_app.config["SITE_INDUSTRY"])}


@bp.patch("/design")
@require_auth(admin=True)
def update_design():
    data = request.get_json(silent=True) or {}
    profile = _active_design_profile()
    if not profile:
        preset = profile_for_industry(data.get("industry") or current_app.config["SITE_INDUSTRY"])
        profile = DesignProfile(
            name=preset["name"],
            status="active",
            source=preset["source"],
            industry=preset["industry"],
            personality=preset["personality"],
            competitor_urls=preset["competitorUrls"],
            tokens=preset["tokens"],
            voice=preset["voice"],
            notes=preset["notes"],
        )
        db.session.add(profile)

    if "name" in data:
        profile.name = data["name"]
    if "source" in data:
        profile.source = data["source"]
    if "industry" in data:
        profile.industry = data["industry"]
    if "personality" in data:
        profile.personality = data["personality"]
    if "competitorUrls" in data:
        profile.competitor_urls = data["competitorUrls"]
    if "tokens" in data and isinstance(data["tokens"], dict):
        profile.tokens = deep_merge(profile.tokens or {}, data["tokens"])
    if "voice" in data and isinstance(data["voice"], dict):
        profile.voice = deep_merge(profile.voice or {}, data["voice"])
    if "notes" in data:
        profile.notes = data["notes"]
    if "sections" in data and isinstance(data["sections"], list):
        profile.sections = data["sections"]

    normalized = normalized_profile(profile.to_dict(), profile.industry or current_app.config["SITE_INDUSTRY"])
    profile.tokens = normalized["tokens"]
    profile.voice = normalized["voice"]
    db.session.commit()
    return {"item": profile.to_dict()}


@bp.post("/design/generate")
@require_auth(admin=True)
def generate_design():
    data = request.get_json(silent=True) or {}
    preset = data.get("preset") or data.get("style")
    generated = apply_style(preset) if preset else None
    if not generated:
        generated = profile_for_industry(
            data.get("industry") or current_app.config["SITE_INDUSTRY"],
            data.get("competitorUrls") or [],
        )
        generated["source"] = "generated-from-industry-and-competitors"
    if data.get("notes"):
        generated["notes"] = data["notes"]

    profile = _active_design_profile()
    if not profile:
        profile = DesignProfile(status="active")
        db.session.add(profile)

    profile.name = generated["name"]
    profile.source = generated["source"]
    profile.industry = generated.get("industry") or current_app.config["SITE_INDUSTRY"]
    profile.personality = generated.get("personality", "")
    profile.competitor_urls = generated.get("competitorUrls", [])
    # Content width is a global preference, not a per-theme aesthetic: keep the user's current
    # contentMaxWidth when switching themes (robust), unless they pass {width|contentMaxWidth}.
    _WIDTHS = {"narrow": "1040px", "standard": "1160px", "wide": "1280px",
               "full": "1440px", "extra-wide": "1440px", "extrawide": "1440px"}
    _prev_w = ((profile.tokens or {}).get("layout") or {}).get("contentMaxWidth")
    _new_tokens = generated["tokens"]
    _want = data.get("width") or data.get("contentMaxWidth")
    _chosen = _WIDTHS.get(str(_want).strip().lower(), _want) if _want else _prev_w
    if _chosen:
        _new_tokens.setdefault("layout", {})["contentMaxWidth"] = _chosen
    profile.tokens = _new_tokens
    profile.voice = generated["voice"]
    profile.notes = generated.get("notes", "")
    profile.sections = generated.get("sections") or []
    db.session.commit()
    return {"item": profile.to_dict()}


@bp.post("/design/analyze-competitors")
@require_auth(admin=True)
def analyze_design_competitors():
    data = request.get_json(silent=True) or {}
    competitor_urls = data.get("competitorUrls") or []
    if not isinstance(competitor_urls, list) or not competitor_urls:
        return jsonify({"error": {"code": "bad_request", "message": "competitorUrls is required"}}), 400
    observations = data.get("observations") or []
    if not isinstance(observations, list):
        return jsonify({"error": {"code": "bad_request", "message": "observations must be a list"}}), 400

    generated = analyze_competitors(
        data.get("industry") or current_app.config["SITE_INDUSTRY"],
        competitor_urls,
        observations=observations,
        notes=data.get("notes") or "",
    )

    profile = _active_design_profile()
    if not profile:
        profile = DesignProfile(status="active")
        db.session.add(profile)

    profile.name = generated["name"]
    profile.source = generated["source"]
    profile.industry = generated["industry"]
    profile.personality = generated["personality"]
    profile.competitor_urls = generated["competitorUrls"]
    profile.tokens = generated["tokens"]
    profile.voice = generated["voice"]
    profile.notes = generated["notes"]
    db.session.commit()
    return {"item": profile.to_dict(), "analysis": generated["analysis"]}


# --- Block composition (manifest-driven, granular page editing) -------------
# Edit any page's block list ("home" = active design profile, or a page slug)
# one block at a time, by stable id. Pure logic lives in block_service.

def _locale_sections(obj, locale):
    """Working copy of an object's sections for `locale`. For a non-default locale
    with no translation yet, seed from a deep copy of the base sections so the
    agent can translate in place (block ids stay aligned with the base)."""
    if not locale:
        return list(obj.sections or [])
    tr = (obj.i18n or {}).get(locale) or {}
    if tr.get("sections") is not None:
        return list(tr["sections"])
    return deepcopy(list(obj.sections or []))


def _resolve_surface(target: str, locale=None):
    """Return (kind, obj, sections) for 'home' (active design profile) or a page
    slug. kind is 'home' | 'page' | None (not found). `sections` is the working
    list for `locale` (base columns when locale is None/default)."""
    if target == "home":
        profile = _active_design_profile()
        if profile is None:
            preset = profile_for_industry(current_app.config["SITE_INDUSTRY"])
            profile = DesignProfile(
                name=preset["name"], status="active", source=preset["source"],
                industry=preset["industry"], personality=preset["personality"],
                competitor_urls=preset["competitorUrls"], tokens=preset["tokens"],
                voice=preset["voice"], notes=preset["notes"], sections=preset.get("sections") or [],
            )
            db.session.add(profile)
            db.session.flush()
        return "home", profile, _locale_sections(profile, locale)
    page = Page.query.filter_by(slug=target).first()
    if page is None:
        return None, None, None
    return "page", page, _locale_sections(page, locale)


def _save_surface(obj, sections, locale=None):
    # JSON column is plain (no mutation tracking) — reassign to persist.
    if locale:
        _set_i18n(obj, locale, {"sections": sections})
    else:
        obj.sections = sections
    db.session.commit()


def _surface_payload(kind, obj, sections, locale=None):
    return {
        "target": "home" if kind == "home" else obj.slug,
        "locale": locale or current_app.config["SITE_DEFAULT_LOCALE"],
        "blocks": block_service.summarize(sections),
    }


def _surface_404(target):
    return jsonify({"error": {"code": "not_found", "message": f"No editable page for target '{target}'."}}), 404


def _block_404(target, block_id):
    return jsonify({"error": {"code": "not_found", "message": f"No block '{block_id}' on '{target}'."}}), 404


@bp.get("/compose/<target>/blocks")
@require_auth(admin=True)
def compose_list(target):
    locale = _admin_locale()
    kind, obj, sections = _resolve_surface(target, locale)
    if kind is None:
        return _surface_404(target)
    if block_service.ensure_ids(sections):
        _save_surface(obj, sections, locale)
    return {"item": _surface_payload(kind, obj, sections, locale)}


@bp.post("/compose/<target>/blocks")
@require_auth(admin=True)
def compose_add(target):
    locale = _admin_locale()
    kind, obj, sections = _resolve_surface(target, locale)
    if kind is None:
        return _surface_404(target)
    data = request.get_json(silent=True) or {}
    block_service.ensure_ids(sections)
    # `pattern` inserts a saved capture; otherwise scaffold a typed block.
    spec = None
    if data.get("pattern"):
        pattern = BlockPattern.query.filter_by(slug=data["pattern"]).first()
        if pattern is None:
            return jsonify({"error": {"code": "not_found", "message": f"No pattern '{data['pattern']}'."}}), 404
        spec = pattern.spec or {}
    try:
        if spec is not None:
            block = block_service.add_block(sections, spec.get("type"), spec.get("variant"), spec.get("content"), data.get("position", "end"))
        else:
            block = block_service.add_block(sections, data.get("type"), data.get("variant"), data.get("content"), data.get("position", "end"))
    except block_service.BlockError as exc:
        return jsonify({"error": {"code": "bad_request", "message": str(exc)}}), 400
    _save_surface(obj, sections, locale)
    return {"item": block, "page": _surface_payload(kind, obj, sections, locale)}, 201


@bp.patch("/compose/<target>/blocks/<block_id>")
@require_auth(admin=True)
def compose_update(target, block_id):
    locale = _admin_locale()
    kind, obj, sections = _resolve_surface(target, locale)
    if kind is None:
        return _surface_404(target)
    block_service.ensure_ids(sections)
    if block_service.find_index(sections, block_id) < 0:
        return _block_404(target, block_id)
    data = request.get_json(silent=True) or {}
    try:
        block = block_service.update_block(
            sections, block_id, data.get("variant"), data.get("content"), bool(data.get("replaceContent", False))
        )
    except block_service.BlockError as exc:
        return jsonify({"error": {"code": "bad_request", "message": str(exc)}}), 400
    _save_surface(obj, sections, locale)
    return {"item": block, "page": _surface_payload(kind, obj, sections, locale)}


@bp.post("/compose/<target>/blocks/<block_id>/move")
@require_auth(admin=True)
def compose_move(target, block_id):
    locale = _admin_locale()
    kind, obj, sections = _resolve_surface(target, locale)
    if kind is None:
        return _surface_404(target)
    block_service.ensure_ids(sections)
    if block_service.find_index(sections, block_id) < 0:
        return _block_404(target, block_id)
    data = request.get_json(silent=True) or {}
    try:
        block = block_service.move_block(sections, block_id, data.get("position", "end"))
    except block_service.BlockError as exc:
        return jsonify({"error": {"code": "bad_request", "message": str(exc)}}), 400
    _save_surface(obj, sections, locale)
    return {"item": block, "page": _surface_payload(kind, obj, sections, locale)}


@bp.post("/compose/<target>/blocks/<block_id>/duplicate")
@require_auth(admin=True)
def compose_duplicate(target, block_id):
    locale = _admin_locale()
    kind, obj, sections = _resolve_surface(target, locale)
    if kind is None:
        return _surface_404(target)
    block_service.ensure_ids(sections)
    if block_service.find_index(sections, block_id) < 0:
        return _block_404(target, block_id)
    block = block_service.duplicate_block(sections, block_id)
    _save_surface(obj, sections, locale)
    return {"item": block, "page": _surface_payload(kind, obj, sections, locale)}, 201


@bp.delete("/compose/<target>/blocks/<block_id>")
@require_auth(admin=True)
def compose_remove(target, block_id):
    locale = _admin_locale()
    kind, obj, sections = _resolve_surface(target, locale)
    if kind is None:
        return _surface_404(target)
    block_service.ensure_ids(sections)
    if block_service.find_index(sections, block_id) < 0:
        return _block_404(target, block_id)
    removed = block_service.remove_block(sections, block_id)
    _save_surface(obj, sections, locale)
    return {"item": {"id": block_id, "type": removed.get("type"), "deleted": True}, "page": _surface_payload(kind, obj, sections, locale)}


@bp.post("/compose/<target>/batch")
@require_auth(admin=True)
def compose_batch(target):
    """Apply many block ops in one call — built for chat (Telegram) where a single
    request ("a pricing page: hero + 3 tiers + FAQ") is several block edits.
    ops: [{op:add|update|move|duplicate|remove, ...}]. atomic (default true):
    all-or-nothing — on any failure nothing is saved and failedAt is returned.
    ?locale=zh edits that locale's section list (seeded from the base on first edit)."""
    locale = _admin_locale()
    kind, obj, sections = _resolve_surface(target, locale)
    if kind is None:
        return _surface_404(target)
    data = request.get_json(silent=True) or {}
    ops = data.get("ops")
    if not isinstance(ops, list) or not ops:
        return jsonify({"error": {"code": "bad_request", "message": "ops must be a non-empty list."}}), 400
    atomic = bool(data.get("atomic", True))

    block_service.ensure_ids(sections)
    working = deepcopy(sections)  # mutate a copy so atomic can discard on failure
    results = []
    for i, op in enumerate(ops):
        op_name = op.get("op") if isinstance(op, dict) else None
        try:
            block = block_service.apply_op(working, op)
            results.append({"index": i, "ok": True, "op": op_name,
                            "id": block.get("id") if isinstance(block, dict) else None})
        except block_service.BlockError as exc:
            results.append({"index": i, "ok": False, "op": op_name, "error": str(exc)})
            if atomic:
                return jsonify({"error": {"code": "bad_request",
                    "message": f"Batch failed at op {i}: {exc} No changes were applied (atomic).",
                    "failedAt": i, "results": results}}), 400

    _save_surface(obj, working, locale)
    return {"item": {"applied": sum(1 for r in results if r["ok"]), "total": len(ops), "results": results},
            "page": _surface_payload(kind, obj, working, locale)}


@bp.get("/surfaces")
@require_auth(admin=True)
def list_surfaces():
    """One call that lists every editable surface — the home composition plus all
    pages (with status) and their blocks. Lets a Telegram bot answer "what can I
    edit?" and pick a target before composing."""
    out = []
    _, home_obj, home_sections = _resolve_surface("home")
    home_changed = block_service.ensure_ids(home_sections)
    if home_changed:
        home_obj.sections = home_sections
    out.append({"target": "home", "kind": "home", "name": home_obj.name,
                "mode": "sections", "locales": sorted((home_obj.i18n or {}).keys()),
                "blocks": block_service.summarize(home_sections)})

    for page in Page.query.order_by(Page.nav_order.asc(), Page.title.asc()).all():
        secs = list(page.sections or [])
        if block_service.ensure_ids(secs):
            page.sections = secs
        out.append({"target": page.slug, "kind": "page", "title": page.title,
                    "status": page.status, "showInNav": page.show_in_nav,
                    "mode": "sections" if secs else "markdown",
                    "locales": sorted((page.i18n or {}).keys()),
                    "blocks": block_service.summarize(secs)})

    db.session.commit()
    return {"items": out, "meta": {"count": len(out),
            "defaultLocale": current_app.config["SITE_DEFAULT_LOCALE"],
            "locales": current_app.config["SITE_LOCALES"]}}


RESERVED_SLUGS = {"blog", "blogs", "contact", "api", "admin", "_next"}


def _create_page(data: dict, publish: bool) -> Page:
    status = "published" if publish else data.get("status", "draft")
    page = Page(
        title=data["title"],
        slug=_unique_slug(data.get("slug") or data["title"], model=Page),
        body_markdown=data.get("body_markdown", ""),
        sections=data.get("sections") or [],
        status=status,
        nav_label=data.get("nav_label", ""),
        nav_order=int(data.get("nav_order", 100)),
        show_in_nav=bool(data.get("show_in_nav", True)),
        meta_title=data.get("meta_title", data["title"][:60]),
        meta_description=data.get("meta_description", "")[:320],
        published_at=datetime.now(timezone.utc) if status == "published" else None,
    )
    page.canonical_url = f"{current_app.config['SITE_URL']}/{page.slug}"
    db.session.add(page)
    db.session.commit()
    return page


@bp.post("/pages")
@require_auth(admin=True)
def create_page():
    data = request.get_json(silent=True) or {}
    if not data.get("title") or (not data.get("body_markdown") and not data.get("sections")):
        return jsonify({"error": {"code": "bad_request", "message": "title and (body_markdown or sections) are required"}}), 400
    if slugify(data.get("slug") or data["title"]) in RESERVED_SLUGS:
        return jsonify({"error": {"code": "bad_request", "message": "slug is reserved"}}), 400
    page = _create_page(data, publish=data.get("status") == "published")
    return {"item": page.to_detail_dict()}, 201


@bp.patch("/pages/<int:page_id>")
@require_auth(admin=True)
def update_page(page_id: int):
    page = db.session.get(Page, page_id)
    if not page:
        return jsonify({"error": {"code": "not_found", "message": "Page not found"}}), 404
    data = request.get_json(silent=True) or {}
    locale = _admin_locale()
    if locale:
        # Translation: localizable fields go into i18n[locale]; nav order / status stay global.
        _set_i18n(page, locale, {k: data[k] for k in
                  ["title", "nav_label", "body_markdown", "sections", "meta_title", "meta_description"] if k in data})
        for key in ["status", "nav_order", "show_in_nav"]:
            if key in data:
                setattr(page, key, data[key])
    else:
        for key in ["title", "body_markdown", "sections", "status", "nav_label", "nav_order", "show_in_nav", "meta_title", "meta_description"]:
            if key in data:
                setattr(page, key, data[key])
    if data.get("status") == "published" and not page.published_at:
        page.published_at = datetime.now(timezone.utc)
    db.session.commit()
    return {"item": page.to_detail_dict(locale)}


@bp.delete("/pages/<int:page_id>")
@require_auth(admin=True)
def delete_page(page_id: int):
    page = db.session.get(Page, page_id)
    if not page:
        return jsonify({"error": {"code": "not_found", "message": "Page not found"}}), 404
    db.session.delete(page)
    db.session.commit()
    return {"item": {"id": page_id, "deleted": True}}


# --- Capture: pattern library (saved reusable section specs) -----------------

@bp.post("/patterns")
@require_auth(admin=True)
def create_pattern():
    """Save a section as a reusable pattern. Provide a full `spec` (a block with a
    'type'), or {target, blockId} to capture a block already on a surface."""
    data = request.get_json(silent=True) or {}
    spec = data.get("spec")
    if not spec and data.get("target") and data.get("blockId"):
        kind, obj, sections = _resolve_surface(data["target"], _admin_locale())
        if kind is None:
            return _surface_404(data["target"])
        idx = block_service.find_index(sections, data["blockId"])
        if idx < 0:
            return _block_404(data["target"], data["blockId"])
        spec = deepcopy(sections[idx])
    if not isinstance(spec, dict) or not spec.get("type"):
        return jsonify({"error": {"code": "bad_request", "message": "spec (a block with a 'type') or {target, blockId} is required"}}), 400
    if not data.get("name"):
        return jsonify({"error": {"code": "bad_request", "message": "name is required"}}), 400
    if not block_service.block_spec(spec.get("type")):
        return jsonify({"error": {"code": "bad_request", "message": f"Unknown block type '{spec.get('type')}'."}}), 400
    spec = deepcopy(spec)
    spec.pop("id", None)  # a pattern is a template, not a live instance
    pattern = BlockPattern(
        name=data["name"],
        slug=_unique_slug(data.get("slug") or data["name"], model=BlockPattern),
        category=data.get("category", "captured"),
        tags=data.get("tags", []),
        spec=spec,
        source=data.get("source", "capture"),
        notes=data.get("notes", ""),
    )
    db.session.add(pattern)
    db.session.commit()
    return {"item": pattern.to_detail_dict()}, 201


@bp.delete("/patterns/<int:pattern_id>")
@require_auth(admin=True)
def delete_pattern(pattern_id: int):
    pattern = db.session.get(BlockPattern, pattern_id)
    if not pattern:
        return jsonify({"error": {"code": "not_found", "message": "Pattern not found"}}), 404
    db.session.delete(pattern)
    db.session.commit()
    return {"item": {"id": pattern_id, "deleted": True}}


# --- i18n: UI chrome strings -------------------------------------------------

@bp.patch("/i18n/<locale>")
@require_auth(admin=True)
def update_ui_messages(locale: str):
    """Edit the UI chrome strings for a locale (nav/footer/buttons). Merges by
    default; pass {"replace": true} to overwrite the whole catalog."""
    locale = (locale or "").strip().lower()
    if locale not in current_app.config["SITE_LOCALES"]:
        return jsonify({"error": {"code": "bad_request",
            "message": f"Unknown locale '{locale}'. Allowed: {', '.join(current_app.config['SITE_LOCALES'])}."}}), 400
    data = request.get_json(silent=True) or {}
    messages = data.get("messages")
    if not isinstance(messages, dict):
        return jsonify({"error": {"code": "bad_request", "message": "messages object is required"}}), 400
    row = UiMessages.query.filter_by(locale=locale).first()
    if row is None:
        row = UiMessages(locale=locale, messages={})
        db.session.add(row)
    merged = {} if data.get("replace") else dict(row.messages or {})
    merged.update(messages)
    row.messages = merged
    db.session.commit()
    return {"item": row.to_dict()}


# --- media: user-uploaded images (hosting only — no generation) --------------
#
# Accepts an image three ways so it works from any client (incl. a Telegram bot):
#   • multipart/form-data with a `file` field        (curl -F "file=@photo.png")
#   • JSON {"url": "https://…"}                       (fetch & store a remote image)
#   • JSON {"data": "<base64>", "filename": "x.png"}  (inline bytes; data: URLs ok)
# Bytes are sniffed by magic number, so a lying extension can't smuggle a
# non-image through and we only ever host raster images.

_IMAGE_SNIFF = (  # (magic-byte test, canonical extension)
    (lambda b: b[:8] == b"\x89PNG\r\n\x1a\n", "png"),
    (lambda b: b[:3] == b"\xff\xd8\xff", "jpg"),
    (lambda b: b[:6] in (b"GIF87a", b"GIF89a"), "gif"),
    (lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP", "webp"),
)
_MEDIA_CT = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}


def _sniff_image_ext(data: bytes):
    for test, ext in _IMAGE_SNIFF:
        try:
            if test(data):
                return ext
        except Exception:
            pass
    return None


def _media_error(msg, status=400, code="bad_request"):
    return jsonify({"error": {"code": code, "message": msg}}), status


@bp.post("/media")
@require_auth(admin=True)
def upload_media():
    """Host a user-uploaded image (no generation). Returns its /api/media/<file>
    URL, ready to drop into a gallery/team/hero block or a blog hero_image_url."""
    max_bytes = current_app.config["MEDIA_MAX_MB"] * 1024 * 1024
    raw = None
    hint_name = None  # caller's suggested filename, if any

    file = request.files.get("file")
    if file is not None:
        raw = file.read()
        hint_name = file.filename
    else:
        data = request.get_json(silent=True) or {}
        if data.get("url"):
            url = str(data["url"]).strip()
            if not url.lower().startswith(("http://", "https://")):
                return _media_error("url must be http(s)")
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "oracle-site-media/1.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = resp.read(max_bytes + 1)
            except Exception as exc:
                return _media_error(f"could not fetch url: {exc}")
            hint_name = os.path.basename(urllib.parse.urlparse(url).path) or None
        elif data.get("data"):
            b64 = str(data["data"])
            if b64.lstrip().startswith("data:") and "," in b64:
                b64 = b64.split(",", 1)[1]  # strip a data: URL prefix
            try:
                raw = base64.b64decode(b64, validate=False)
            except Exception:
                return _media_error("data is not valid base64")
            hint_name = data.get("filename")
        else:
            return _media_error("provide a multipart `file`, or JSON {url} or {data}")

    if not raw:
        return _media_error("empty upload")
    if len(raw) > max_bytes:
        return _media_error(
            f"image too large ({len(raw) // 1024} KB); limit is {current_app.config['MEDIA_MAX_MB']} MB",
            413, "payload_too_large")

    ext = _sniff_image_ext(raw)
    if ext is None:
        return _media_error("not a supported image (png, jpg, gif, webp only)")

    base = os.path.splitext(secure_filename(hint_name or "image"))[0][:48].strip("-_.") or "image"
    name = f"{base}-{secrets.token_hex(4)}.{ext}"
    media_dir = current_app.config["MEDIA_DIR"]
    os.makedirs(media_dir, exist_ok=True)
    with open(os.path.join(media_dir, name), "wb") as fh:
        fh.write(raw)

    # Absolute URL (the frontend host has no /api proxy, so an <img src> must point
    # at the API host). `path` is the relative form for any same-origin use.
    return jsonify({"item": {
        "filename": name,
        "url": f"{current_app.config['API_PUBLIC_URL']}/api/media/{name}",
        "path": f"/api/media/{name}",
        "bytes": len(raw),
        "contentType": _MEDIA_CT[ext],
    }}), 201


@bp.get("/media")
@require_auth(admin=True)
def list_media():
    """List hosted images (name, URL, size) so the agent can reuse what's already uploaded."""
    media_dir = current_app.config["MEDIA_DIR"]
    base = current_app.config["API_PUBLIC_URL"]
    items = []
    if os.path.isdir(media_dir):
        for name in sorted(os.listdir(media_dir)):
            path = os.path.join(media_dir, name)
            if os.path.isfile(path) and not name.startswith("."):
                items.append({"filename": name, "url": f"{base}/api/media/{name}",
                              "path": f"/api/media/{name}", "bytes": os.path.getsize(path)})
    return {"items": items}


@bp.delete("/media/<path:filename>")
@require_auth(admin=True)
def delete_media(filename: str):
    """Delete a hosted image by filename."""
    safe = secure_filename(filename)
    if not safe:
        return _media_error("bad filename")
    path = os.path.join(current_app.config["MEDIA_DIR"], safe)
    if not os.path.isfile(path):
        return _media_error("file not found", 404, "not_found")
    os.remove(path)
    return {"item": {"filename": safe, "deleted": True}}
