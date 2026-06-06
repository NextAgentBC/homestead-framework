"""Every real-business industry must resolve to a complete, image-ready home —
a photo hero + a gallery, stable block ids, and an imagery spec the rebrand
pipeline can generate against. (Aesthetic style presets like 'minimal' are looks,
not industries, and are intentionally exempt.)"""
from app.services import design_service as d

INDUSTRIES = sorted(set(d.INDUSTRY_STYLE_ALIASES.values()) | {"education", "nonprofit", "finance"})


def test_every_industry_is_complete_and_image_ready():
    for ind in INDUSTRIES:
        prof = d.profile_for_industry(ind)
        secs = prof.get("sections") or []
        types = [s.get("type") for s in secs]
        assert len(secs) >= 8, f"{ind}: only {len(secs)} sections"
        assert "hero" in types and "gallery" in types, f"{ind}: missing hero/gallery ({types})"
        assert all(s.get("id") for s in secs), f"{ind}: every block needs a stable id"
        assert prof.get("images"), f"{ind}: needs an imagery spec for the rebrand pipeline"


def test_industry_aliases_resolve_to_rich_templates():
    # A few common synonyms should land on the same complete template.
    for alias, expected in [("dentist", "healthcare"), ("gym", "fitness"),
                            ("cafe", "restaurant"), ("salon", "beauty"), ("lawyer", "legal")]:
        prof = d.profile_for_industry(alias)
        types = [s.get("type") for s in (prof.get("sections") or [])]
        assert "gallery" in types, f"alias {alias!r} did not resolve to a rich template"
