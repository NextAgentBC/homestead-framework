from datetime import datetime, timezone
from typing import Optional

from flask import Blueprint, current_app, jsonify, request
from slugify import slugify

from ..auth import require_auth
from ..extensions import db
from ..models import BlogPost, DesignProfile
from ..services.ai_service import generate_blog_post
from ..services.design_service import deep_merge, profile_for_industry

bp = Blueprint("admin", __name__)


def _active_design_profile() -> Optional[DesignProfile]:
    return DesignProfile.query.filter_by(status="active").order_by(DesignProfile.updated_at.desc()).first()


def _unique_slug(slug: str) -> str:
    base = slugify(slug) or "post"
    candidate = base
    index = 2
    while BlogPost.query.filter_by(slug=candidate).first():
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
    return {"item": profile.to_dict()}


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
    if "tokens" in data:
        profile.tokens = deep_merge(profile.tokens or {}, data["tokens"])
    if "voice" in data:
        profile.voice = deep_merge(profile.voice or {}, data["voice"])
    if "notes" in data:
        profile.notes = data["notes"]

    db.session.commit()
    return {"item": profile.to_dict()}


@bp.post("/design/generate")
@require_auth(admin=True)
def generate_design():
    data = request.get_json(silent=True) or {}
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
    profile.industry = generated["industry"]
    profile.personality = generated["personality"]
    profile.competitor_urls = generated["competitorUrls"]
    profile.tokens = generated["tokens"]
    profile.voice = generated["voice"]
    profile.notes = generated["notes"]
    db.session.commit()
    return {"item": profile.to_dict()}
