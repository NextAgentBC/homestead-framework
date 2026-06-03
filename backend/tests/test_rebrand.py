"""Tests for POST /api/admin/site/rebrand — the atomic industry switch."""
import pytest

from app.extensions import db
from app.models import DesignProfile, Page


def _seed(app):
    with app.app_context():
        db.session.add(DesignProfile(
            name="Old", status="active", industry="education",
            sections=[{"id": "b1", "type": "hero", "content": {"headline": "Old"}}],
            i18n={"zh": {"sections": [{"id": "b1", "type": "hero", "content": {"headline": "旧"}}]}}))
        db.session.add(Page(
            title="About", slug="about", body_markdown="x", status="published",
            sections=[{"id": "p1", "type": "hero", "content": {"headline": "About"}}],
            i18n={"zh": {"title": "关于", "sections": [{"id": "p1", "type": "hero", "content": {"headline": "关于"}}]}}))
        db.session.commit()


def test_rebrand_switches_industry_and_drops_stale_locale_sections(client, auth, app):
    _seed(app)
    res = client.post("/api/admin/site/rebrand", headers=auth, json={"industry": "restaurant"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["item"]["industry"] == "restaurant"
    assert body["item"]["name"]  # regenerated a profile name
    assert "summary" in body.get("audit", {})
    assert body["pagesTouched"] == 1
    with app.app_context():
        prof = DesignProfile.query.filter_by(status="active").first()
        assert "sections" not in (prof.i18n.get("zh") or {})       # stale home zh structure dropped
        page = Page.query.filter_by(slug="about").first()
        assert "sections" not in (page.i18n.get("zh") or {})       # stale page zh structure dropped
        assert (page.i18n.get("zh") or {}).get("title") == "关于"   # other localized fields preserved


def test_rebrand_brandname_override(client, auth, app):
    _seed(app)
    res = client.post("/api/admin/site/rebrand", headers=auth,
                      json={"industry": "restaurant", "brandName": "Trattoria Uno"})
    assert res.get_json()["item"]["name"] == "Trattoria Uno"


def test_rebrand_dryrun_does_not_write(client, auth, app):
    _seed(app)
    res = client.post("/api/admin/site/rebrand", headers=auth, json={"industry": "restaurant", "dryRun": True})
    assert res.status_code == 200
    assert res.get_json()["item"]["dryRun"] is True
    with app.app_context():
        prof = DesignProfile.query.filter_by(status="active").first()
        assert prof.industry == "education"                 # unchanged
        assert "sections" in (prof.i18n.get("zh") or {})    # still present


def test_rebrand_requires_industry_or_preset(client, auth):
    res = client.post("/api/admin/site/rebrand", headers=auth, json={})
    assert res.status_code == 400


def test_beauty_template_is_complete_and_image_ready(client, auth):
    """配齐: rebrand to beauty yields the full image-ready home + declared imagery."""
    res = client.post("/api/admin/site/rebrand", headers=auth, json={"industry": "beauty"})
    assert res.status_code == 200
    body = res.get_json()
    sections = body["item"]["sections"]
    types = [s["type"] for s in sections]
    assert len(sections) >= 9
    assert types[0] == "hero" and "gallery" in types and "steps" in types and "pricing" in types
    hero = sections[0]
    assert hero["variant"] == "fullbleed" and "image" in hero["content"]   # image slot present
    assert hero["content"].get("imagePrompt")                              # empty slot shows its prompt
    gallery = next(s for s in sections if s["type"] == "gallery")
    assert all(it.get("imagePrompt") for it in gallery["content"]["items"])  # every gallery slot prompted
    imgs = body["imagery"]["images"]
    assert len(imgs) == 6
    assert all(("prompt" in i and "aspect" in i and "block" in i) for i in imgs)
    assert body["imagery"]["style"]   # shared style string for tonal cohesion


@pytest.mark.parametrize("industry,prefix", [
    ("restaurant", "rest"), ("healthcare", "clin"), ("legal", "law"), ("fitness", "fit")])
def test_other_industry_templates_are_complete_and_image_ready(client, auth, industry, prefix):
    """配齐: the common industries match the beauty bar — full image-ready home + imagery."""
    res = client.post("/api/admin/site/rebrand", headers=auth, json={"industry": industry})
    assert res.status_code == 200
    body = res.get_json()
    sections = body["item"]["sections"]
    assert [s["type"] for s in sections] == [
        "hero", "stats", "features", "gallery", "steps", "testimonials", "pricing", "faq", "cta"]
    assert sections[0]["variant"] == "fullbleed" and sections[0]["id"] == f"b_{prefix}_hero"
    assert sections[0]["content"].get("imagePrompt")   # empty hero slot carries its prompt
    imgs = body["imagery"]["images"]
    assert len(imgs) == 6 and body["imagery"]["style"]
    ids = {s["id"] for s in sections}
    assert all(i["block"] in ids for i in imgs)   # every image targets a real block
