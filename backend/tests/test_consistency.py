"""Tests for the site-coherence audit (consistency_service) + its admin route."""
from app.extensions import db
from app.models import DesignProfile, Page
from app.services.consistency_service import run_audit


def _home(base_sections, zh_sections=None):
    s = {"name": "home", "kind": "home", "base": {"sections": base_sections, "text": {}}, "i18n": {}}
    if zh_sections is not None:
        s["i18n"] = {"zh": {"sections": zh_sections}}
    return s


def _hero(bid, headline, subhead):
    return {"id": bid, "type": "hero", "content": {"headline": headline, "subhead": subhead}}


def test_clean_site_has_no_findings():
    home = _home([_hero("b1", "Welcome", "A calm skincare studio in Vancouver")],
                 [_hero("b1", "欢迎", "温哥华一家安静的护肤工作室")])
    res = run_audit([home], "en", ["en", "zh"], "beauty")
    assert res["ok"] is True
    assert res["findings"] == []


def test_structural_drift_when_locale_blocks_differ():
    home = _home([_hero("b1", "Welcome", "Calm skincare studio")],
                 [_hero("b_other", "欢迎", "护肤工作室"), _hero("b2", "x", "y")])
    res = run_audit([home], "en", ["en", "zh"], "beauty")
    kinds = {f["kind"] for f in res["findings"]}
    assert "structural_drift" in kinds
    assert res["ok"] is False


def test_missing_translation_when_locale_text_equals_base():
    home = _home([_hero("b1", "Welcome", "A calm skincare studio in Vancouver")],
                 [_hero("b1", "Welcome", "A calm skincare studio in Vancouver")])  # untranslated
    res = run_audit([home], "en", ["en", "zh"], "beauty")
    assert any(f["kind"] == "missing_translation" for f in res["findings"])


def test_language_mismatch_cjk_in_default_locale():
    home = _home([_hero("b1", "核心护理项目", "深层清洁与补水修护护理")],
                 [_hero("b1", "核心护理项目", "深层清洁与补水修护护理")])
    res = run_audit([home], "en", ["en", "zh"], "beauty")
    assert any(f["kind"] == "language_mismatch" and f["locale"] == "en" for f in res["findings"])


def test_language_mismatch_no_cjk_in_zh():
    home = _home([_hero("b1", "Signature treatments", "Facials and skin coaching for you")],
                 [_hero("b1", "标志护理", "Facials and skin coaching for everyone here")])  # zh value still English
    res = run_audit([home], "en", ["en", "zh"], "beauty")
    assert any(f["kind"] == "language_mismatch" and f["locale"] == "zh" for f in res["findings"])


def test_industry_residue_term_flagged():
    home = _home([_hero("b1", "Built with OpenClaw", "A website framework demo")],
                 [_hero("b1", "用 OpenClaw 构建", "一个网站框架演示")])
    res = run_audit([home], "en", ["en", "zh"], "beauty")
    assert any(f["kind"] == "industry_residue" for f in res["findings"])


def test_trivial_strings_not_flagged_as_untranslated():
    # prices/ratings/short tokens are legitimately identical across locales
    block = {"id": "b1", "type": "stats", "content": {"items": [
        {"value": "$68", "label": "Price"}, {"value": "4.9★", "label": "Rating"}]}}
    zh = {"id": "b1", "type": "stats", "content": {"items": [
        {"value": "$68", "label": "价格"}, {"value": "4.9★", "label": "评分"}]}}
    res = run_audit([_home([block], [zh])], "en", ["en", "zh"], "beauty")
    # "$68"/"4.9★" must NOT produce missing_translation findings
    assert all("$68" not in f["detail"] and "4.9" not in f["detail"] for f in res["findings"])


def test_endpoint_returns_audit(client, auth, app):
    with app.app_context():
        db.session.add(DesignProfile(
            name="Lumière", status="active", industry="beauty",
            sections=[_hero("b1", "Welcome", "A calm skincare studio in Vancouver")],
            i18n={"zh": {"sections": [_hero("b1", "欢迎", "温哥华一家安静的护肤工作室")]}}))
        db.session.add(Page(title="About", slug="about", body_markdown="About us here.",
                            status="published", sections=[],
                            i18n={"zh": {"title": "关于", "body_markdown": "关于我们。"}}))
        db.session.commit()
    res = client.get("/api/admin/consistency", headers=auth)
    assert res.status_code == 200
    item = res.get_json()["item"]
    assert "findings" in item and "ok" in item and "summary" in item
    assert item["defaultLocale"] == "en" and "zh" in item["locales"]
