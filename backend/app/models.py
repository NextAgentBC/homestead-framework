from datetime import datetime, timezone

from .extensions import db


def _pick(i18n: dict, locale, field, base):
    """Resolve a localized field: i18n[locale][field] if present & non-empty,
    else the base-column value (the default locale). locale=None → base."""
    if not locale:
        return base
    tr = (i18n or {}).get(locale) or {}
    val = tr.get(field)
    if val is None or val == "":
        return base
    return val


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class User(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, default="")
    picture = db.Column(db.Text, nullable=False, default="")
    google_sub = db.Column(db.String(255), unique=True, nullable=False, index=True)
    role = db.Column(db.String(32), nullable=False, default="user")

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "role": self.role,
        }


class BlogPost(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    excerpt = db.Column(db.Text, nullable=False, default="")
    body_markdown = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="draft")
    author = db.Column(db.String(255), nullable=False, default="Editorial")
    tags = db.Column(db.JSON, nullable=False, default=list)
    meta_title = db.Column(db.String(255), nullable=False, default="")
    meta_description = db.Column(db.String(320), nullable=False, default="")
    canonical_url = db.Column(db.Text, nullable=False, default="")
    geo_region = db.Column(db.String(255), nullable=False, default="")
    published_at = db.Column(db.DateTime, nullable=True)
    # {"<locale>": {"title":..,"excerpt":..,"body_markdown":..,"tags":[..],"meta_title":..,"meta_description":..}}
    i18n = db.Column(db.JSON, nullable=False, default=dict)

    def to_card_dict(self, locale=None) -> dict:
        return {
            "id": self.id,
            "title": _pick(self.i18n, locale, "title", self.title),
            "slug": self.slug,
            "excerpt": _pick(self.i18n, locale, "excerpt", self.excerpt),
            "tags": _pick(self.i18n, locale, "tags", self.tags),
            "author": self.author,
            "publishedAt": self.published_at.isoformat() if self.published_at else None,
            "metaTitle": _pick(self.i18n, locale, "meta_title", self.meta_title),
            "metaDescription": _pick(self.i18n, locale, "meta_description", self.meta_description),
            "canonicalUrl": self.canonical_url,
            "geoRegion": self.geo_region,
            "locales": sorted((self.i18n or {}).keys()),
        }

    def to_detail_dict(self, locale=None) -> dict:
        item = self.to_card_dict(locale)
        item["bodyMarkdown"] = _pick(self.i18n, locale, "body_markdown", self.body_markdown)
        item["status"] = self.status
        return item


class Page(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    body_markdown = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="draft")
    nav_label = db.Column(db.String(255), nullable=False, default="")
    nav_order = db.Column(db.Integer, nullable=False, default=100)
    show_in_nav = db.Column(db.Boolean, nullable=False, default=True)
    sections = db.Column(db.JSON, nullable=False, default=list)
    meta_title = db.Column(db.String(255), nullable=False, default="")
    meta_description = db.Column(db.String(320), nullable=False, default="")
    canonical_url = db.Column(db.Text, nullable=False, default="")
    published_at = db.Column(db.DateTime, nullable=True)
    # {"<locale>": {"title":..,"nav_label":..,"body_markdown":..,"sections":[..],"meta_title":..,"meta_description":..}}
    i18n = db.Column(db.JSON, nullable=False, default=dict)

    def to_card_dict(self, locale=None) -> dict:
        title = _pick(self.i18n, locale, "title", self.title)
        return {
            "id": self.id,
            "title": title,
            "slug": self.slug,
            "navLabel": _pick(self.i18n, locale, "nav_label", self.nav_label) or title,
            "navOrder": self.nav_order,
            "showInNav": self.show_in_nav,
            "metaTitle": _pick(self.i18n, locale, "meta_title", self.meta_title),
            "metaDescription": _pick(self.i18n, locale, "meta_description", self.meta_description),
            "locales": sorted((self.i18n or {}).keys()),
        }

    def to_detail_dict(self, locale=None) -> dict:
        item = self.to_card_dict(locale)
        item["bodyMarkdown"] = _pick(self.i18n, locale, "body_markdown", self.body_markdown)
        item["status"] = self.status
        item["canonicalUrl"] = self.canonical_url
        item["publishedAt"] = self.published_at.isoformat() if self.published_at else None
        item["sections"] = _pick(self.i18n, locale, "sections", self.sections)
        return item


class NewsletterSubscription(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, default="")
    status = db.Column(db.String(32), nullable=False, default="active")
    source = db.Column(db.String(255), nullable=False, default="website")


class DesignProfile(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="active", index=True)
    source = db.Column(db.String(255), nullable=False, default="default")
    industry = db.Column(db.String(255), nullable=False, default="")
    personality = db.Column(db.Text, nullable=False, default="")
    competitor_urls = db.Column(db.JSON, nullable=False, default=list)
    tokens = db.Column(db.JSON, nullable=False, default=dict)
    voice = db.Column(db.JSON, nullable=False, default=dict)
    notes = db.Column(db.Text, nullable=False, default="")
    sections = db.Column(db.JSON, nullable=False, default=list)
    # {"<locale>": {"sections": [..localized home blocks..]}}
    i18n = db.Column(db.JSON, nullable=False, default=dict)

    def to_dict(self, locale=None) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "source": self.source,
            "industry": self.industry,
            "personality": self.personality,
            "competitorUrls": self.competitor_urls,
            "tokens": self.tokens,
            "voice": self.voice,
            "notes": self.notes,
            "sections": _pick(self.i18n, locale, "sections", self.sections),
            "availableLocales": sorted((self.i18n or {}).keys()),
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class SiteSettings(TimestampMixin, db.Model):
    """Singleton (id=1) runtime site identity — brand name, industry, audience,
    region, and the live-chat assistant's name. Stored in the DB (not just env)
    so a rebrand / "switch industry" can change the whole site's identity —
    nav + footer brand, blog lede, SEO, and the chat persona — with **no
    redeploy**. Any blank field falls back to the matching ``SITE_*`` env; see
    ``services.site_service.effective()``. The ``assistant_name`` falls back to
    the brand name when blank (so the chat helper introduces itself as the site)."""
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(255), nullable=False, default="")
    industry = db.Column(db.String(255), nullable=False, default="")
    audience = db.Column(db.String(255), nullable=False, default="")
    region = db.Column(db.String(255), nullable=False, default="")
    assistant_name = db.Column(db.String(255), nullable=False, default="")

    def to_dict(self) -> dict:
        return {
            "siteName": self.site_name,
            "industry": self.industry,
            "audience": self.audience,
            "region": self.region,
            "assistantName": self.assistant_name,
        }


class UiMessages(TimestampMixin, db.Model):
    """UI chrome strings (nav/footer/buttons) per locale, so even the framework
    labels are not hard-coded — the agent can edit them with no redeploy. The
    frontend ships English defaults and overlays whatever this returns."""
    id = db.Column(db.Integer, primary_key=True)
    locale = db.Column(db.String(16), unique=True, nullable=False, index=True)
    messages = db.Column(db.JSON, nullable=False, default=dict)

    def to_dict(self) -> dict:
        return {"locale": self.locale, "messages": self.messages or {}}


class BlockPattern(TimestampMixin, db.Model):
    """A saved, reusable section spec — the 'capture' library. A pattern's `spec`
    is a full block ({type, variant, content}); inserting it scaffolds a new
    instance. Lets the block vocabulary grow from screenshots with no redeploy."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    category = db.Column(db.String(64), nullable=False, default="captured")
    tags = db.Column(db.JSON, nullable=False, default=list)
    spec = db.Column(db.JSON, nullable=False, default=dict)
    source = db.Column(db.String(255), nullable=False, default="capture")
    notes = db.Column(db.Text, nullable=False, default="")

    def to_card_dict(self) -> dict:
        spec = self.spec or {}
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "category": self.category,
            "tags": self.tags,
            "type": spec.get("type"),
            "variant": spec.get("variant"),
            "source": self.source,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_detail_dict(self) -> dict:
        item = self.to_card_dict()
        item["spec"] = self.spec or {}
        item["notes"] = self.notes
        return item


class Revision(TimestampMixin, db.Model):
    """A point-in-time snapshot of an editable *surface*, captured **before** each
    change so an edit can be undone or rolled back ("撤销 / 回到上一版") with no
    redeploy. A surface is "home" (the active design profile's section list),
    "page:<slug>" (a content page's sections), or "design" (the whole active
    design profile — tokens + voice + sections, snapshotted on a theme switch).
    History is capped per (surface, locale); see `revision_service`."""
    __tablename__ = "revision"

    id = db.Column(db.Integer, primary_key=True)
    surface = db.Column(db.String(128), nullable=False, index=True)  # home | page:<slug> | design
    locale = db.Column(db.String(16), nullable=False, default="")    # "" = default/base locale
    kind = db.Column(db.String(16), nullable=False, default="sections")  # sections | design
    label = db.Column(db.String(255), nullable=False, default="")    # what the change was
    snapshot = db.Column(db.JSON, nullable=False, default=dict)       # prior state (list or dict)

    def to_card_dict(self) -> dict:
        snap = self.snapshot
        if isinstance(snap, list):
            blocks = len(snap)
        elif isinstance(snap, dict):
            blocks = len(snap.get("sections") or []) if "sections" in snap else None
        else:
            blocks = None
        return {
            "id": self.id,
            "surface": self.surface,
            "locale": self.locale,
            "kind": self.kind,
            "label": self.label,
            "blocks": blocks,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

    def to_detail_dict(self) -> dict:
        item = self.to_card_dict()
        item["snapshot"] = self.snapshot
        return item


class ChatConversation(TimestampMixin, db.Model):
    """One website chat thread, keyed by a browser-generated session id. The bot
    brain is the (tool-less) OpenClaw model turn run by the host webchat-bridge;
    this just persists the transcript + any captured lead so the operator can
    review and take over from Telegram."""
    __tablename__ = "chat_conversation"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    status = db.Column(db.String(32), nullable=False, default="open")  # open | closed
    locale = db.Column(db.String(16), nullable=False, default="")
    visitor_name = db.Column(db.String(255), nullable=False, default="")
    visitor_email = db.Column(db.String(255), nullable=False, default="")
    last_message_at = db.Column(db.DateTime, nullable=True)
    meta = db.Column(db.JSON, nullable=False, default=dict)  # {ua, referrer, page, ipHash}
    messages = db.relationship(
        "ChatMessage",
        backref="conversation",
        order_by="ChatMessage.id",
        cascade="all, delete-orphan",
    )

    def to_card_dict(self) -> dict:
        msgs = list(self.messages)
        last = msgs[-1] if msgs else None
        return {
            "id": self.id,
            "sessionId": self.session_id,
            "status": self.status,
            "locale": self.locale,
            "visitorName": self.visitor_name,
            "visitorEmail": self.visitor_email,
            "messageCount": len(msgs),
            "lastMessage": (last.text[:160] if last else ""),
            "lastRole": (last.role if last else ""),
            "lastMessageAt": self.last_message_at.isoformat() if self.last_message_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

    def to_detail_dict(self) -> dict:
        item = self.to_card_dict()
        item["messages"] = [m.to_dict() for m in self.messages]
        item["meta"] = self.meta or {}
        return item


class ChatMessage(TimestampMixin, db.Model):
    __tablename__ = "chat_message"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("chat_conversation.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = db.Column(db.String(16), nullable=False, default="visitor")  # visitor | agent | operator
    text = db.Column(db.Text, nullable=False, default="")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "text": self.text,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
