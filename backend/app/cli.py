from datetime import datetime, timedelta, timezone
from typing import Optional

import click
from flask import current_app

from .auth import issue_jwt
from .extensions import db
from .models import BlogPost, User
from .routes.admin import _create_post
from .services import site_service
from .services.ai_service import generate_blog_post

@click.group("blog")
def blog_cli():
    """Blog operations."""


@blog_cli.command("generate-daily")
@click.option("--topic", default=None)
@click.option("--draft", is_flag=True)
def generate_daily(topic: Optional[str], draft: bool):
    generated = generate_blog_post(topic)
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
