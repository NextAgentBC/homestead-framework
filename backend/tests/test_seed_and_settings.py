"""Tests for the first-boot seed + runtime site identity (SiteSettings):
a fresh deploy becomes a real multi-page site, and brand/industry/audience/assistant
are DB-backed so a rebrand or a settings PATCH changes the whole site with no redeploy."""
from app.extensions import db
from app.models import DesignProfile, Page
from app.services import site_service


def test_seed_creates_rich_home_and_starter_pages(app):
    created = site_service.seed_demo()
    assert any("home design" in c for c in created)
    assert "page:about" in created and "page:services" in created
    # A real, multi-section home — not a stub.
    prof = DesignProfile.query.filter_by(status="active").first()
    assert prof is not None and len(prof.sections) >= 5
    # The nav is a real menu, not just Blog + Contact.
    assert {"about", "services"} <= {p.slug for p in Page.query.all()}


def test_seed_is_idempotent(app):
    assert site_service.seed_demo()            # first run creates content
    assert site_service.seed_demo() == []      # second run adds nothing
    assert DesignProfile.query.count() == 1
    assert Page.query.filter(Page.slug.in_(["about", "services"])).count() == 2


def test_site_endpoint_assistant_follows_brand(client):
    # No SiteSettings row yet → identity comes from env, assistant follows the brand.
    body = client.get("/api/site").get_json()["item"]
    assert "assistantName" in body
    assert body["assistantName"] == body["name"]


def test_update_site_settings_takes_effect(client, auth):
    res = client.patch("/api/admin/site/settings", headers=auth,
                       json={"siteName": "Lumière", "industry": "beauty", "audience": "skincare clients"})
    assert res.status_code == 200
    body = client.get("/api/site").get_json()["item"]
    assert body["name"] == "Lumière"
    assert body["industry"] == "beauty"
    assert body["audience"] == "skincare clients"
    assert body["assistantName"] == "Lumière"          # follows brand while unset
    # An explicit assistant name overrides the brand-follow.
    client.patch("/api/admin/site/settings", headers=auth, json={"assistantName": "Lily"})
    assert client.get("/api/site").get_json()["item"]["assistantName"] == "Lily"


def test_rebrand_updates_site_identity(client, auth):
    db.session.add(DesignProfile(name="Old", status="active", industry="education", sections=[]))
    db.session.commit()
    res = client.post("/api/admin/site/rebrand", headers=auth,
                      json={"industry": "restaurant", "brandName": "Trattoria Sole", "audience": "local families"})
    assert res.status_code == 200
    site = client.get("/api/site").get_json()["item"]
    assert site["industry"] == "restaurant"
    assert site["name"] == "Trattoria Sole"
    assert site["audience"] == "local families"
    assert site["assistantName"] == "Trattoria Sole"   # assistant follows the new brand
