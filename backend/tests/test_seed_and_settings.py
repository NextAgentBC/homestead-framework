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


def test_nap_settings_roundtrip(client, auth):
    """The full NAP set survives PATCH → public GET /api/site field-for-field
    (real Vancouver Power Wash Pro data). NAP has no env fallback: unset fields
    come back empty, and what the admin stores is exactly what JSON-LD gets."""
    # Before anything is stored, every NAP field is explicitly empty (no env leak).
    empty = client.get("/api/site").get_json()["item"]["nap"]
    assert empty["legalName"] == "" and empty["phone"] == ""
    assert empty["latitude"] is None and empty["longitude"] is None
    assert empty["hours"] == [] and empty["serviceAreas"] == []

    hours = [{"days": ["Mo", "Tu", "We", "Th", "Fr", "Sa"], "opens": "09:00", "closes": "18:00"}]
    payload = {
        "legalName": "Vancouver Power Wash Pro",
        "phone": "778-259-4555",
        "email": "info@vancouverwashpro.ca",
        "addressStreet": "Unit 36, 1959 165A St",
        "addressCity": "Surrey",
        "addressRegion": "BC",
        "addressPostalCode": "V3Z 1K3",
        "addressCountry": "CA",
        "latitude": 49.031,
        "longitude": -122.756,
        "businessHours": hours,
        "serviceAreas": ["Surrey", "Vancouver", "Burnaby", "Richmond", "Coquitlam"],
    }
    res = client.patch("/api/admin/site/settings", headers=auth, json=payload)
    assert res.status_code == 200
    assert set(payload) <= set(res.get_json()["item"]["changed"])

    nap = client.get("/api/site").get_json()["item"]["nap"]
    assert nap["legalName"] == "Vancouver Power Wash Pro"
    assert nap["phone"] == "778-259-4555"
    assert nap["email"] == "info@vancouverwashpro.ca"
    assert nap["street"] == "Unit 36, 1959 165A St"
    assert nap["city"] == "Surrey"
    assert nap["region"] == "BC"
    assert nap["postalCode"] == "V3Z 1K3"
    assert nap["country"] == "CA"
    assert nap["latitude"] == 49.031
    assert nap["longitude"] == -122.756
    assert nap["hours"] == hours
    assert nap["serviceAreas"] == ["Surrey", "Vancouver", "Burnaby", "Richmond", "Coquitlam"]


def test_page_local_business_overrides_roundtrip(client, auth):
    """A page's local_business_overrides (city×service narrowing for JSON-LD)
    persists through create and comes back on the public detail — not on cards."""
    overrides = {"service_areas": ["Surrey"], "service_type": "Pressure Washing"}
    res = client.post("/api/admin/pages", headers=auth,
                      json={"title": "Pressure Washing in Surrey", "slug": "pressure-washing-surrey",
                            "body_markdown": "Driveways, siding, and decks.", "status": "published",
                            "local_business_overrides": overrides})
    assert res.status_code == 201
    assert res.get_json()["item"]["localBusinessOverrides"] == overrides

    item = client.get("/api/pages/pressure-washing-surrey").get_json()["item"]
    assert item["localBusinessOverrides"] == overrides
    # Card payloads stay lean — the override only rides on the detail.
    cards = client.get("/api/pages").get_json()["items"]
    assert all("localBusinessOverrides" not in c for c in cards)
