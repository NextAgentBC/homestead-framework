from app.services.competitor_analyzer import analyze_competitors, fetch_competitor_snapshot
from app.services.design_service import normalized_profile


def test_fetch_rejects_private_urls():
    result = fetch_competitor_snapshot("http://127.0.0.1:8000")
    assert result["error"] == "Only http and https URLs are supported"


def test_analyzer_uses_observation_tokens_and_ignores_bad_colors():
    profile = analyze_competitors(
        "retail",
        [],
        observations=[
            {
                "colors": ["not-a-color", "#a6422b", "#28666e"],
                "fonts": ["Nunito Sans"],
                "signals": {"hasShop": True},
            }
        ],
    )

    assert profile["source"] == "competitor-analyzer"
    assert profile["tokens"]["colors"]["primary"] == "#a6422b"
    assert profile["tokens"]["typography"]["body"].startswith("Nunito Sans")
    assert profile["tokens"]["layout"]["heroMinHeight"] == "60vh"


def test_normalized_profile_fills_missing_design_tokens():
    profile = normalized_profile({"tokens": {"colors": {"primary": "#123456"}}}, "accounting")

    assert profile["tokens"]["colors"]["primary"] == "#123456"
    assert profile["tokens"]["colors"]["ink"]
    assert profile["tokens"]["typography"]["body"]
    assert profile["tokens"]["layout"]["contentMaxWidth"]

