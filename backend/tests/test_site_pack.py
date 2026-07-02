"""Round-trip tests for site packs (`flask site export` / `site import`).

A site pack is the way a hand-tuned industry sample becomes a fast template for
the next client. These tests pin the three properties that make that safe:
  • media URLs are portable — rewritten to the `__MEDIA__/` sentinel in the pack
    and back to the *new* site's API base on import (never bound to a domain);
  • the referenced media *files* ride along inside the pack;
  • NAP contact info NEVER travels in a pack (a pack is a template, not a client
    identity), while the generic identity (name/industry/audience/region) does.

The round-trip runs against the conftest temp-SQLite app: seed a customized
site → export to a tmp tar.gz → wipe the DB + media dir (simulating a fresh
deploy) → import with a NEW api-base → assert everything came back correctly.
"""
import json
import os
import tarfile

from app.extensions import db
from app.models import DesignProfile, Page, SiteSettings, UiMessages

SRC_API = "https://old-api.example.com"
NEW_API = "https://new-api.example.com"


def _media_url(name: str, base: str = SRC_API) -> str:
    return f"{base}/api/media/{name}"


def _use_tmp_media_dir(app, tmp_path):
    """Point MEDIA_DIR at a writable temp dir (the default /app/media is not
    writable in tests). Call inside the app context before seeding."""
    media_dir = os.path.join(str(tmp_path), "media")
    app.config["MEDIA_DIR"] = media_dir
    os.makedirs(media_dir, exist_ok=True)
    return media_dir


def _seed_customized_site(app):
    """A realistic customized site: an active design with a hero image, a page
    with a gallery image, a full NAP on SiteSettings, and one UI-messages row."""
    media_dir = app.config["MEDIA_DIR"]
    os.makedirs(media_dir, exist_ok=True)
    # A tiny (fake) media file the sections reference by absolute URL.
    with open(os.path.join(media_dir, "hero.png"), "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\nHEROPIXELS")
    with open(os.path.join(media_dir, "gallery.jpg"), "wb") as fh:
        fh.write(b"\xff\xd8\xffGALLERYPIXELS")

    design = DesignProfile(
        name="Sparkle Home Services",
        status="active",
        source="hand-tuned",
        industry="construction",
        personality="trustworthy, local",
        competitor_urls=["https://competitor.example.com"],
        tokens={"colors": {"primary": "#0af"}},
        voice={"tone": "friendly"},
        notes="A carefully tuned sample.",
        sections=[
            {"id": "b1", "type": "hero", "content": {"image": _media_url("hero.png"),
                                                     "title": "Book a job today"}},
        ],
        i18n={"zh": {"sections": [
            {"id": "b1", "type": "hero", "content": {"image": _media_url("hero.png"),
                                                     "title": "立即预约"}}]}},
    )
    db.session.add(design)

    page = Page(
        title="Gallery", slug="gallery", body_markdown="Our work.",
        status="published", nav_label="Gallery", nav_order=30, show_in_nav=True,
        sections=[{"id": "g1", "type": "gallery",
                   "content": {"images": [_media_url("gallery.jpg")]}}],
        meta_title="Gallery", meta_description="Recent jobs",
        local_business_overrides={"service_areas": ["Surrey"]},
    )
    db.session.add(page)

    db.session.add(UiMessages(locale="en", messages={"nav.home": "Home"}))

    # A full NAP — none of this may leak into the pack.
    settings = SiteSettings(
        id=1, site_name="Sparkle Home Services", industry="construction",
        audience="homeowners", region="British Columbia",
        legal_name="Sparkle Home Services Ltd.", phone="+1-555-0100",
        email="secret@sparkle.example.com", address_street="1 Secret Rd",
        address_city="Surrey", address_region="BC", address_postal_code="V1V 1V1",
        address_country="CA", latitude=49.1, longitude=-122.8,
        business_hours=[{"days": ["Mo"], "opens": "09:00", "closes": "17:00"}],
        service_areas=["Surrey", "Vancouver"],
    )
    db.session.add(settings)
    db.session.commit()


def _reset_site(app):
    """Simulate a fresh deploy: drop every row + wipe the media dir."""
    db.drop_all()
    db.create_all()
    media_dir = app.config["MEDIA_DIR"]
    for name in list(os.listdir(media_dir)) if os.path.isdir(media_dir) else []:
        os.remove(os.path.join(media_dir, name))


def _export(app, out_path, include_blog=False):
    args = ["site", "export", "--out", str(out_path)]
    if include_blog:
        args.append("--include-blog")
    return app.test_cli_runner().invoke(args=args)


def _import(app, pack_path, rebrand_name=None, api_base=NEW_API, force=False):
    args = ["site", "import", str(pack_path), "--api-base", api_base]
    if rebrand_name:
        args += ["--rebrand-name", rebrand_name]
    if force:
        args.append("--force")
    return app.test_cli_runner().invoke(args=args)


def _manifest(pack_path) -> dict:
    with tarfile.open(pack_path, "r:gz") as tar:
        return json.loads(tar.extractfile("manifest.json").read().decode("utf-8"))


def test_manifest_rewrites_media_to_sentinel_and_excludes_nap(app, tmp_path):
    """Export: media URLs become the sentinel; NAP is entirely absent; only the
    generic identity travels."""
    with app.app_context():
        _use_tmp_media_dir(app, tmp_path)
        _seed_customized_site(app)
        pack = tmp_path / "pack.tar.gz"
        res = _export(app, pack)
        assert res.exit_code == 0, res.output

    manifest = _manifest(pack)

    # Media rewritten to sentinel in both base and i18n sections — no absolute URL.
    blob = json.dumps(manifest)
    assert "__MEDIA__/hero.png" in blob
    assert "__MEDIA__/gallery.jpg" in blob
    assert SRC_API not in blob                      # the source domain is gone
    assert "/api/media/" not in blob                # no absolute media URL survives
    assert set(manifest["media"]) == {"hero.png", "gallery.jpg"}

    # siteIdentity has ONLY the generic fields.
    assert manifest["siteIdentity"] == {
        "site_name": "Sparkle Home Services", "industry": "construction",
        "audience": "homeowners", "region": "British Columbia",
    }
    # NAP must not appear anywhere in the pack. (Note: a *page's*
    # local_business_overrides legitimately carries a "service_areas" key — that's
    # per-page city×service narrowing, not the business's NAP; here we assert the
    # SiteSettings NAP *values* and NAP-only field names are gone. "Vancouver" is
    # unique to the SiteSettings service_areas, so it is a clean leak sentinel.)
    for leak in ("secret@sparkle.example.com", "+1-555-0100", "1 Secret Rd",
                 "V1V 1V1", "Vancouver", "legalName", "legal_name",
                 "\"phone\"", "latitude", "longitude",
                 "businessHours", "business_hours"):
        assert leak not in blob, f"NAP leak in pack: {leak!r}"
    # The design/siteIdentity carry no NAP subtrees at all.
    assert "nap" not in manifest and "siteIdentity" in manifest
    assert set(manifest["siteIdentity"].keys()) == {"site_name", "industry", "audience", "region"}


def test_media_files_ride_along_in_pack(app, tmp_path):
    with app.app_context():
        _use_tmp_media_dir(app, tmp_path)
        _seed_customized_site(app)
        pack = tmp_path / "pack.tar.gz"
        assert _export(app, pack).exit_code == 0

    with tarfile.open(pack, "r:gz") as tar:
        names = set(tar.getnames())
    assert "media/hero.png" in names
    assert "media/gallery.jpg" in names


def test_round_trip_restores_design_pages_media_and_rewrites_urls(app, tmp_path):
    """Full round-trip: export → wipe → import with a NEW api-base. Design and
    pages come back, media files are restored, sentinels are rewritten to the new
    base, and NAP stays unset (must be configured per client)."""
    with app.app_context():
        _use_tmp_media_dir(app, tmp_path)
        _seed_customized_site(app)
        pack = tmp_path / "pack.tar.gz"
        assert _export(app, pack).exit_code == 0

        _reset_site(app)
        assert DesignProfile.query.count() == 0
        assert Page.query.count() == 0

        res = _import(app, pack, api_base=NEW_API)
        assert res.exit_code == 0, res.output

        # Design restored, media URL rewritten to the NEW api-base (not the old one).
        design = DesignProfile.query.filter_by(status="active").first()
        assert design is not None
        assert design.name == "Sparkle Home Services"
        assert design.sections[0]["content"]["image"] == _media_url("hero.png", NEW_API)
        assert SRC_API not in json.dumps(design.sections)
        assert "__MEDIA__" not in json.dumps(design.sections)
        # i18n sections rewritten too.
        assert design.i18n["zh"]["sections"][0]["content"]["image"] == _media_url("hero.png", NEW_API)

        # Page restored with its gallery image rewritten + overrides intact.
        page = Page.query.filter_by(slug="gallery").first()
        assert page is not None
        assert page.sections[0]["content"]["images"] == [_media_url("gallery.jpg", NEW_API)]
        assert page.local_business_overrides == {"service_areas": ["Surrey"]}

        # UI messages restored.
        ui = UiMessages.query.filter_by(locale="en").first()
        assert ui is not None and ui.messages == {"nav.home": "Home"}

        # Generic identity restored; NAP explicitly NOT (still empty on the new site).
        row = db.session.get(SiteSettings, 1)
        assert row.site_name == "Sparkle Home Services"
        assert row.industry == "construction"
        assert row.phone == "" and row.email == "" and row.legal_name == ""
        assert row.latitude is None and row.business_hours == [] and row.service_areas == []

    # Media files were written back into the fresh media dir.
    media_dir = app.config["MEDIA_DIR"]
    assert os.path.isfile(os.path.join(media_dir, "hero.png"))
    assert os.path.isfile(os.path.join(media_dir, "gallery.jpg"))


def test_rebrand_name_overrides_site_name(app, tmp_path):
    with app.app_context():
        _use_tmp_media_dir(app, tmp_path)
        _seed_customized_site(app)
        pack = tmp_path / "pack.tar.gz"
        assert _export(app, pack).exit_code == 0
        _reset_site(app)
        assert _import(app, pack, rebrand_name="Bright Wash Co").exit_code == 0
        row = db.session.get(SiteSettings, 1)
        assert row.site_name == "Bright Wash Co"       # rebrand wins over the pack
        assert row.industry == "construction"          # other identity still from the pack


def test_page_slug_conflict_skips_without_force(app, tmp_path):
    with app.app_context():
        _use_tmp_media_dir(app, tmp_path)
        _seed_customized_site(app)
        pack = tmp_path / "pack.tar.gz"
        assert _export(app, pack).exit_code == 0

        # Keep the DB (do NOT reset): 'gallery' already exists → import must skip it,
        # leaving the existing page's body untouched.
        existing = Page.query.filter_by(slug="gallery").first()
        existing.body_markdown = "LOCAL EDIT"
        db.session.commit()

        res = _import(app, pack)      # no --force
        assert res.exit_code == 0
        assert "already exists" in res.output
        assert Page.query.filter_by(slug="gallery").count() == 1
        assert Page.query.filter_by(slug="gallery").first().body_markdown == "LOCAL EDIT"

        # With --force the page is overwritten from the pack.
        res = _import(app, pack, force=True)
        assert res.exit_code == 0
        assert Page.query.filter_by(slug="gallery").first().body_markdown == "Our work."


def test_include_blog_flag_controls_blog_in_pack(app, tmp_path):
    from app.models import BlogPost
    with app.app_context():
        _use_tmp_media_dir(app, tmp_path)
        _seed_customized_site(app)
        db.session.add(BlogPost(title="Published Post", slug="published-post",
                                body_markdown="Body", status="published"))
        db.session.add(BlogPost(title="Draft Post", slug="draft-post",
                                body_markdown="Body", status="draft"))
        db.session.commit()

        without = tmp_path / "no-blog.tar.gz"
        assert _export(app, without).exit_code == 0
        assert "blog" not in _manifest(without)

        with_blog = tmp_path / "with-blog.tar.gz"
        assert _export(app, with_blog, include_blog=True).exit_code == 0
        blog = _manifest(with_blog)["blog"]
        slugs = {p["slug"] for p in blog}
        assert "published-post" in slugs        # published rides along
        assert "draft-post" not in slugs        # drafts do not
