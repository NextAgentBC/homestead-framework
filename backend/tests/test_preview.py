"""Visitor industry-preview demo: /industries lists the templates, /design/preview
returns a full industry template WITHOUT persisting anything (the real design is
untouched), and /site exposes the demoPreview flag for the frontend to gate on."""
from app.models import DesignProfile


def test_industries_lists_templates(client):
    items = client.get("/api/industries").get_json()["items"]
    keys = {i["key"] for i in items}
    assert {"beauty", "education", "restaurant", "fitness", "legal"} <= keys
    assert all(i.get("name") for i in items)


def test_design_preview_is_full_and_nonpersistent(client, app):
    pv = client.get("/api/design/preview?industry=restaurant").get_json()["item"]
    types = [s.get("type") for s in (pv.get("sections") or [])]
    assert "hero" in types and "gallery" in types and len(types) >= 8
    assert "restaurant" in (pv.get("source") or "") or pv.get("industry") == "restaurant"
    # The preview must not write anything to the database.
    with app.app_context():
        assert DesignProfile.query.count() == 0


def test_site_demo_preview_flag_default_off(client):
    # Default config leaves the demo off; the flag is still present for the frontend.
    assert client.get("/api/site").get_json()["item"]["demoPreview"] is False
