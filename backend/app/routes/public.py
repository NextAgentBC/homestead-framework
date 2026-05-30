from datetime import datetime, timezone

import json
from importlib.resources import files

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import text

from ..auth import issue_jwt, upsert_google_user, verify_google_token
from ..extensions import db
from ..models import BlogPost, DesignProfile, NewsletterSubscription
from ..services.design_service import DEFAULT_DESIGN_PROFILE
from ..services.email_service import send_email

bp = Blueprint("public", __name__)


@bp.get("/health")
def health():
    db.session.execute(text("select 1"))
    return {"status": "ok", "database": "ok"}


@bp.get("/site")
def site():
    return {
        "item": {
            "name": current_app.config["SITE_NAME"],
            "url": current_app.config["SITE_URL"],
            "industry": current_app.config["SITE_INDUSTRY"],
            "audience": current_app.config["SITE_AUDIENCE"],
            "region": current_app.config["SITE_REGION"],
            "googleClientId": current_app.config["GOOGLE_CLIENT_ID"],
        }
    }


@bp.get("/design")
def design():
    profile = DesignProfile.query.filter_by(status="active").order_by(DesignProfile.updated_at.desc()).first()
    return {"item": profile.to_dict() if profile else DEFAULT_DESIGN_PROFILE}


@bp.get("/openapi.json")
def openapi():
    spec = files("app").joinpath("openapi.json").read_text(encoding="utf-8")
    return jsonify(json.loads(spec))


@bp.post("/auth/google")
def google_auth():
    data = request.get_json(silent=True) or {}
    credential = data.get("credential", "")
    if not credential:
        return jsonify({"error": {"code": "bad_request", "message": "Missing Google credential"}}), 400
    try:
        payload = verify_google_token(credential)
        user = upsert_google_user(payload)
    except ValueError as exc:
        return jsonify({"error": {"code": "bad_request", "message": str(exc)}}), 400
    return {"item": {"user": user.to_public_dict(), "token": issue_jwt(user)}}


@bp.get("/blogs")
def blogs():
    posts = (
        BlogPost.query.filter_by(status="published")
        .order_by(BlogPost.published_at.desc().nullslast(), BlogPost.created_at.desc())
        .all()
    )
    return {"items": [post.to_card_dict() for post in posts], "meta": {"count": len(posts)}}


@bp.get("/blogs/<slug>")
def blog_detail(slug: str):
    post = BlogPost.query.filter_by(slug=slug, status="published").first_or_404()
    return {"item": post.to_detail_dict()}


@bp.post("/newsletter/subscribe")
def subscribe():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    name = data.get("name", "").strip()
    if "@" not in email:
        return jsonify({"error": {"code": "bad_request", "message": "Valid email is required"}}), 400
    subscription = NewsletterSubscription.query.filter_by(email=email).first()
    if not subscription:
        subscription = NewsletterSubscription(email=email, name=name)
        db.session.add(subscription)
    else:
        subscription.name = name or subscription.name
        subscription.status = "active"
    db.session.commit()
    send_email(
        email,
        f"Welcome to {current_app.config['SITE_NAME']}",
        "Thanks for subscribing. You will receive practical updates and daily essays from the site.",
    )
    return {"item": {"email": subscription.email, "status": subscription.status}}


@bp.post("/contact")
def contact():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()
    if not email or not message:
        return jsonify({"error": {"code": "bad_request", "message": "Email and message are required"}}), 400
    admin = next(iter(current_app.config["ADMIN_EMAILS"]), current_app.config["EMAIL_FROM"])
    if admin:
        send_email(admin, "New website contact message", f"From: {email}\n\n{message}")
    return {"item": {"receivedAt": datetime.now(timezone.utc).isoformat()}}
