from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional

from flask import Blueprint, current_app, jsonify, request
from slugify import slugify

from ..auth import require_auth
from ..extensions import db
from ..models import BlogPost, DesignProfile, Page
from ..services.ai_service import generate_blog_post
from ..services.competitor_analyzer import analyze_competitors
from ..services.design_service import apply_style, deep_merge, normalized_profile, profile_for_industry
from ..services import block_service

bp = Blueprint("admin", __name__)


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
    for key in ["title", "excerpt", "body_markdown", "status", "tags", "meta_title", "meta_description", "geo_region"]:
        if key in data:
            setattr(post, key, data[key])
    if data.get("status") == "published" and not post.published_at:
        post.published_at = datetime.now(timezone.utc)
    db.session.commit()
    return {"item": post.to_detail_dict()}


@bp.get("/design")
@require_auth(admin=True)
def get_design():
    profile = _active_design_profile()
    if not profile:
        data = profile_for_industry(current_app.config["SITE_INDUSTRY"])
        return {"item": data}
    return {"item": normalized_profile(profile.to_dict(), profile.industry or current_app.config["SITE_INDUSTRY"])}


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
    profile.tokens = generated["tokens"]
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

def _resolve_surface(target: str):
    """Return (kind, obj, sections) for 'home' (active design profile) or a page
    slug. kind is 'home' | 'page' | None (not found)."""
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
        return "home", profile, list(profile.sections or [])
    page = Page.query.filter_by(slug=target).first()
    if page is None:
        return None, None, None
    return "page", page, list(page.sections or [])


def _save_surface(obj, sections):
    # JSON column is plain (no mutation tracking) — reassign to persist.
    obj.sections = sections
    db.session.commit()


def _surface_payload(kind, obj, sections):
    return {"target": "home" if kind == "home" else obj.slug, "blocks": block_service.summarize(sections)}


def _surface_404(target):
    return jsonify({"error": {"code": "not_found", "message": f"No editable page for target '{target}'."}}), 404


def _block_404(target, block_id):
    return jsonify({"error": {"code": "not_found", "message": f"No block '{block_id}' on '{target}'."}}), 404


@bp.get("/compose/<target>/blocks")
@require_auth(admin=True)
def compose_list(target):
    kind, obj, sections = _resolve_surface(target)
    if kind is None:
        return _surface_404(target)
    if block_service.ensure_ids(sections):
        _save_surface(obj, sections)
    return {"item": _surface_payload(kind, obj, sections)}


@bp.post("/compose/<target>/blocks")
@require_auth(admin=True)
def compose_add(target):
    kind, obj, sections = _resolve_surface(target)
    if kind is None:
        return _surface_404(target)
    data = request.get_json(silent=True) or {}
    block_service.ensure_ids(sections)
    try:
        block = block_service.add_block(
            sections, data.get("type"), data.get("variant"), data.get("content"), data.get("position", "end")
        )
    except block_service.BlockError as exc:
        return jsonify({"error": {"code": "bad_request", "message": str(exc)}}), 400
    _save_surface(obj, sections)
    return {"item": block, "page": _surface_payload(kind, obj, sections)}, 201


@bp.patch("/compose/<target>/blocks/<block_id>")
@require_auth(admin=True)
def compose_update(target, block_id):
    kind, obj, sections = _resolve_surface(target)
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
    _save_surface(obj, sections)
    return {"item": block, "page": _surface_payload(kind, obj, sections)}


@bp.post("/compose/<target>/blocks/<block_id>/move")
@require_auth(admin=True)
def compose_move(target, block_id):
    kind, obj, sections = _resolve_surface(target)
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
    _save_surface(obj, sections)
    return {"item": block, "page": _surface_payload(kind, obj, sections)}


@bp.post("/compose/<target>/blocks/<block_id>/duplicate")
@require_auth(admin=True)
def compose_duplicate(target, block_id):
    kind, obj, sections = _resolve_surface(target)
    if kind is None:
        return _surface_404(target)
    block_service.ensure_ids(sections)
    if block_service.find_index(sections, block_id) < 0:
        return _block_404(target, block_id)
    block = block_service.duplicate_block(sections, block_id)
    _save_surface(obj, sections)
    return {"item": block, "page": _surface_payload(kind, obj, sections)}, 201


@bp.delete("/compose/<target>/blocks/<block_id>")
@require_auth(admin=True)
def compose_remove(target, block_id):
    kind, obj, sections = _resolve_surface(target)
    if kind is None:
        return _surface_404(target)
    block_service.ensure_ids(sections)
    if block_service.find_index(sections, block_id) < 0:
        return _block_404(target, block_id)
    removed = block_service.remove_block(sections, block_id)
    _save_surface(obj, sections)
    return {"item": {"id": block_id, "type": removed.get("type"), "deleted": True}, "page": _surface_payload(kind, obj, sections)}


@bp.post("/compose/<target>/batch")
@require_auth(admin=True)
def compose_batch(target):
    """Apply many block ops in one call — built for chat (Telegram) where a single
    request ("a pricing page: hero + 3 tiers + FAQ") is several block edits.
    ops: [{op:add|update|move|duplicate|remove, ...}]. atomic (default true):
    all-or-nothing — on any failure nothing is saved and failedAt is returned."""
    kind, obj, sections = _resolve_surface(target)
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

    _save_surface(obj, working)
    return {"item": {"applied": sum(1 for r in results if r["ok"]), "total": len(ops), "results": results},
            "page": _surface_payload(kind, obj, working)}


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
                "mode": "sections", "blocks": block_service.summarize(home_sections)})

    for page in Page.query.order_by(Page.nav_order.asc(), Page.title.asc()).all():
        secs = list(page.sections or [])
        if block_service.ensure_ids(secs):
            page.sections = secs
        out.append({"target": page.slug, "kind": "page", "title": page.title,
                    "status": page.status, "showInNav": page.show_in_nav,
                    "mode": "sections" if secs else "markdown",
                    "blocks": block_service.summarize(secs)})

    db.session.commit()
    return {"items": out, "meta": {"count": len(out)}}


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
    for key in ["title", "body_markdown", "sections", "status", "nav_label", "nav_order", "show_in_nav", "meta_title", "meta_description"]:
        if key in data:
            setattr(page, key, data[key])
    if data.get("status") == "published" and not page.published_at:
        page.published_at = datetime.now(timezone.utc)
    db.session.commit()
    return {"item": page.to_detail_dict()}


@bp.delete("/pages/<int:page_id>")
@require_auth(admin=True)
def delete_page(page_id: int):
    page = db.session.get(Page, page_id)
    if not page:
        return jsonify({"error": {"code": "not_found", "message": "Page not found"}}), 404
    db.session.delete(page)
    db.session.commit()
    return {"item": {"id": page_id, "deleted": True}}
