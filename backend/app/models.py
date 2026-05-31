from datetime import datetime, timezone

from .extensions import db


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

    def to_card_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "excerpt": self.excerpt,
            "tags": self.tags,
            "author": self.author,
            "publishedAt": self.published_at.isoformat() if self.published_at else None,
            "metaTitle": self.meta_title,
            "metaDescription": self.meta_description,
            "canonicalUrl": self.canonical_url,
            "geoRegion": self.geo_region,
        }

    def to_detail_dict(self) -> dict:
        item = self.to_card_dict()
        item["bodyMarkdown"] = self.body_markdown
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
    meta_title = db.Column(db.String(255), nullable=False, default="")
    meta_description = db.Column(db.String(320), nullable=False, default="")
    canonical_url = db.Column(db.Text, nullable=False, default="")
    published_at = db.Column(db.DateTime, nullable=True)

    def to_card_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "navLabel": self.nav_label or self.title,
            "navOrder": self.nav_order,
            "showInNav": self.show_in_nav,
            "metaTitle": self.meta_title,
            "metaDescription": self.meta_description,
        }

    def to_detail_dict(self) -> dict:
        item = self.to_card_dict()
        item["bodyMarkdown"] = self.body_markdown
        item["status"] = self.status
        item["canonicalUrl"] = self.canonical_url
        item["publishedAt"] = self.published_at.isoformat() if self.published_at else None
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

    def to_dict(self) -> dict:
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
            "sections": self.sections,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
