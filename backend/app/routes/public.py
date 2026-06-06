from datetime import datetime, timedelta, timezone

import hashlib
import json
import re
import secrets
from importlib.resources import files

import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from sqlalchemy import text

from ..auth import issue_jwt, upsert_google_user, verify_google_token
from ..extensions import db
from ..models import (
    BlockPattern,
    BlogPost,
    ChatConversation,
    ChatMessage,
    DesignProfile,
    NewsletterSubscription,
    Page,
    UiMessages,
)
from ..services.design_service import DEFAULT_DESIGN_PROFILE, normalized_profile, profile_for_industry, demo_industries
from ..services import block_service, chat_service, site_service
from ..services.email_service import send_email

bp = Blueprint("public", __name__)

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SESSION_RE = re.compile(r"[^A-Za-z0-9_-]")


def request_locale():
    """The validated ?locale= query arg, or None for the default locale (which
    means 'use base columns'). Keeps content selection in one place."""
    loc = (request.args.get("locale") or "").strip().lower()
    if not loc or loc == current_app.config["SITE_DEFAULT_LOCALE"]:
        return None
    if loc not in current_app.config["SITE_LOCALES"]:
        return None
    return loc


@bp.get("/health")
def health():
    db.session.execute(text("select 1"))
    return {"status": "ok", "database": "ok"}


@bp.get("/media/<path:filename>")
def media(filename: str):
    """Serve self-hosted media (blog images, etc.) from MEDIA_DIR — a persistent
    volume so the site owns its images instead of hot-linking an external CDN.
    send_from_directory guards against path traversal."""
    media_dir = current_app.config["MEDIA_DIR"]
    os.makedirs(media_dir, exist_ok=True)
    return send_from_directory(media_dir, filename, max_age=86400)


@bp.get("/site")
def site():
    cfg = current_app.config
    s = site_service.effective()
    return {
        "item": {
            "name": s["site_name"],
            "url": cfg["SITE_URL"],
            "industry": s["industry"],
            "audience": s["audience"],
            "region": s["region"],
            "assistantName": s["assistant_name"],
            "googleClientId": cfg["GOOGLE_CLIENT_ID"],
            "locales": cfg["SITE_LOCALES"],
            "defaultLocale": cfg["SITE_DEFAULT_LOCALE"],
            "demoPreview": cfg["SITE_DEMO_PREVIEW"],
        }
    }


@bp.get("/design")
def design():
    locale = request_locale()
    profile = DesignProfile.query.filter_by(status="active").order_by(DesignProfile.updated_at.desc()).first()
    if not profile:
        return {"item": DEFAULT_DESIGN_PROFILE}
    return {"item": normalized_profile(profile.to_dict(locale), profile.industry or current_app.config["SITE_INDUSTRY"])}


@bp.get("/industries")
def industries():
    """Industry templates available for the visitor preview demo (key + display name)."""
    return {"items": demo_industries()}


@bp.get("/design/preview")
def design_preview():
    """Non-destructive preview: return the full design profile for a given industry
    template WITHOUT persisting anything — the real active design is untouched. Powers
    the visitor 'try an industry' demo (cookie-scoped on the frontend)."""
    industry = (request.args.get("industry") or "").strip().lower()
    prof = profile_for_industry(industry)
    return {"item": normalized_profile(prof, prof.get("industry") or industry)}


@bp.get("/i18n/<locale>")
def ui_messages(locale: str):
    """UI chrome strings for a locale (nav/footer/buttons). The frontend ships
    English defaults and overlays whatever is returned here — so even framework
    labels are editable by the agent, no redeploy."""
    locale = (locale or "").strip().lower()
    row = UiMessages.query.filter_by(locale=locale).first()
    return {"item": {"locale": locale, "messages": row.messages if row else {}}}


@bp.get("/patterns")
def patterns():
    """Public catalog of saved section patterns — the growing 'capture' library."""
    items = BlockPattern.query.order_by(BlockPattern.updated_at.desc()).all()
    return {"items": [p.to_card_dict() for p in items], "meta": {"count": len(items)}}


@bp.get("/patterns/<slug>")
def pattern_detail(slug: str):
    pattern = BlockPattern.query.filter_by(slug=slug).first_or_404()
    return {"item": pattern.to_detail_dict()}


@bp.get("/blocks")
def blocks_catalog():
    """Public block catalog — the typed-block library a page can be composed from.
    Lets an agent (or a future visual editor) discover types, variants, fields,
    defaults, and the icon vocabulary, then validate before composing."""
    items = block_service.manifest()
    return {"items": items, "icons": block_service.ICONS, "meta": {"count": len(items)}}


@bp.get("/page-templates")
def page_templates_catalog():
    """Page recipes — the block library organized by page (home/about/services/...).
    Each is a recommended composition; scaffold one with POST /admin/pages {template:"<name>"}."""
    items = block_service.list_page_templates()
    return {"items": items, "meta": {"count": len(items)}}


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
    locale = request_locale()
    posts = (
        BlogPost.query.filter_by(status="published")
        .order_by(BlogPost.published_at.desc().nullslast(), BlogPost.created_at.desc())
        .all()
    )
    return {"items": [post.to_card_dict(locale) for post in posts], "meta": {"count": len(posts)}}


@bp.get("/blogs/<slug>")
def blog_detail(slug: str):
    locale = request_locale()
    post = BlogPost.query.filter_by(slug=slug, status="published").first_or_404()
    return {"item": post.to_detail_dict(locale)}


@bp.get("/pages")
def pages():
    locale = request_locale()
    items = (
        Page.query.filter_by(status="published")
        .order_by(Page.nav_order.asc(), Page.title.asc())
        .all()
    )
    return {"items": [page.to_card_dict(locale) for page in items], "meta": {"count": len(items)}}


@bp.get("/pages/<slug>")
def page_detail(slug: str):
    locale = request_locale()
    page = Page.query.filter_by(slug=slug, status="published").first_or_404()
    return {"item": page.to_detail_dict(locale)}


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
        f"Welcome to {site_service.effective()['site_name']}",
        "Thanks for subscribing. You will receive practical updates and daily essays from the site.",
    )
    return {"item": {"email": subscription.email, "status": subscription.status}}


@bp.post("/contact")
def contact():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    name = (data.get("name") or "").strip()
    message = data.get("message", "").strip()
    if not email or not message:
        return jsonify({"error": {"code": "bad_request", "message": "Email and message are required"}}), 400
    admin = next(iter(current_app.config["ADMIN_EMAILS"]), current_app.config["EMAIL_FROM"])
    if admin:
        try:
            send_email(admin, "New website contact message", f"From: {email}\n\n{message}")
        except Exception as exc:  # noqa: BLE001 — SMTP misconfig must not 500 the form
            current_app.logger.warning("contact email failed: %s", str(exc)[:200])
    # Ping the operator on Telegram too (best-effort) so the assistant surfaces the lead live.
    who = f"{name} <{email}>" if name else email
    chat_service.notify_operator(f"📨 网站留言\n来自：{who}\n\n{message[:1500]}")
    return {"item": {"receivedAt": datetime.now(timezone.utc).isoformat()}}


# ---------------------------------------------------------------------------
# Website live chat — answered by the (tool-less) assistant brain via the host bridge.
# ---------------------------------------------------------------------------

def _clean_session_id(raw, *, generate=False):
    sid = _SESSION_RE.sub("", (raw or "").strip())[:64]
    if not sid and generate:
        sid = "web_" + secrets.token_urlsafe(16).replace("-", "").replace("_", "")[:18]
    return sid


def _visitor_meta(data: dict) -> dict:
    ip = (request.headers.get("CF-Connecting-IP")
          or (request.headers.get("X-Forwarded-For", "").split(",")[0].strip())
          or request.remote_addr or "")
    return {
        "ua": (request.headers.get("User-Agent") or "")[:300],
        "page": (data.get("page") or "")[:300],
        "ipHash": hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16] if ip else "",
    }


def _rate_exceeded(convo: ChatConversation) -> bool:
    limit = current_app.config["WEBCHAT_RATE_PER_MIN"]
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=60)
    recent = (
        ChatMessage.query.filter(
            ChatMessage.conversation_id == convo.id,
            ChatMessage.role == "visitor",
            ChatMessage.created_at >= cutoff,
        ).count()
    )
    return recent >= limit


def _maybe_capture_email(convo: ChatConversation, text_in: str) -> None:
    if convo.visitor_email:
        return
    m = _EMAIL_RE.search(text_in or "")
    if m:
        convo.visitor_email = m.group(0)[:255]


def _fallback_reply(locale) -> str:
    if (locale or "").startswith("zh"):
        return "抱歉，我这边暂时连不上助手。你可以留下邮箱，我们会尽快联系你 🙏"
    return "Sorry, the assistant is briefly unavailable. Leave your email and we'll get back to you soon 🙏"


@bp.post("/chat")
def chat_send():
    if not current_app.config.get("WEBCHAT_ENABLED"):
        return jsonify({"error": {"code": "disabled", "message": "Chat is unavailable."}}), 503
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": {"code": "bad_request", "message": "message is required"}}), 400
    message = message[: current_app.config["WEBCHAT_MAX_MSG_CHARS"]]
    locale = request_locale() or (data.get("locale") or "")
    session_id = _clean_session_id(data.get("sessionId"), generate=True)

    convo = ChatConversation.query.filter_by(session_id=session_id).first()
    if convo is None:
        convo = ChatConversation(session_id=session_id, locale=locale or "", meta=_visitor_meta(data))
        db.session.add(convo)
        db.session.flush()

    if _rate_exceeded(convo):
        return jsonify({"error": {"code": "rate_limited", "message": "Please slow down a moment."}}), 429
    if len(convo.messages) >= current_app.config["WEBCHAT_MAX_TURNS"]:
        return jsonify({"error": {"code": "conversation_full", "message": "Please start a new chat."}}), 409

    history = [{"role": m.role, "text": m.text} for m in convo.messages]
    db.session.add(ChatMessage(conversation_id=convo.id, role="visitor", text=message))
    _maybe_capture_email(convo, message)
    convo.last_message_at = datetime.now(timezone.utc)
    db.session.commit()

    prompt = chat_service.build_prompt(history, message, locale or None)
    reply, degraded = chat_service.ask(prompt, session_id, message)
    if not reply:
        reply, degraded = _fallback_reply(locale), True

    agent_msg = ChatMessage(conversation_id=convo.id, role="agent", text=reply)
    db.session.add(agent_msg)
    convo.last_message_at = datetime.now(timezone.utc)
    db.session.commit()

    return {"item": {"sessionId": session_id, "reply": reply, "messageId": agent_msg.id, "degraded": degraded}}


@bp.get("/chat/<session_id>")
def chat_history(session_id: str):
    sid = _clean_session_id(session_id)
    convo = ChatConversation.query.filter_by(session_id=sid).first() if sid else None
    if convo is None:
        return {"item": {"sessionId": session_id, "status": "open", "messages": []}}
    return {
        "item": {
            "sessionId": convo.session_id,
            "status": convo.status,
            "messages": [m.to_dict() for m in convo.messages],
        }
    }
