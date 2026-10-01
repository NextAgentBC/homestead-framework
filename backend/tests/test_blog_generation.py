"""AI blog drafts: without a model nothing is generated or published (no canned
"operating notes" posing as the site's own article); with one, the post is saved."""
import json

import pytest

from app.models import BlogPost
from app.services import ai_service


class FakeModelResponse:
    def __init__(self, article):
        self.article = article

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": json.dumps(self.article)}}]}


ARTICLE = {"title": "How long does a kitchen renovation take?", "slug": "", "excerpt": "Usually three weeks.",
           "body_markdown": "## Short answer\n\nUsually three weeks.", "tags": ["kitchen"],
           "meta_title": "Kitchen renovation timeline", "meta_description": "What to expect, week by week."}


def test_generating_without_a_model_creates_nothing(app, client, auth):
    app.config["DEEPSEEK_API_KEY"] = ""
    response = client.post("/api/admin/blogs/generate", json={"topic": "renovation", "publish": True}, headers=auth)
    assert response.status_code == 503 and response.json["error"]["code"] == "ai_unavailable"
    with app.app_context():
        assert BlogPost.query.count() == 0


def test_the_daily_job_skips_without_a_model(app):
    app.config["DEEPSEEK_API_KEY"] = ""
    result = app.test_cli_runner().invoke(args=["blog", "generate-daily"])
    assert result.exit_code == 0 and "skipped" in result.output
    with app.app_context():
        assert BlogPost.query.count() == 0


def test_a_model_failure_is_reported_not_raised(app, client, auth, monkeypatch):
    app.config["DEEPSEEK_API_KEY"] = "test-key"

    def broken(*_args, **_kwargs):
        raise ai_service.requests.ConnectionError("down")

    monkeypatch.setattr(ai_service.requests, "post", broken)
    response = client.post("/api/admin/blogs/generate", json={}, headers=auth)
    assert response.status_code == 502 and response.json["error"]["code"] == "ai_failed"


@pytest.mark.parametrize("publish,status", [(False, "draft"), (True, "published")])
def test_with_a_model_the_post_is_saved(app, client, auth, monkeypatch, publish, status):
    app.config["DEEPSEEK_API_KEY"] = "test-key"
    monkeypatch.setattr(ai_service.requests, "post", lambda *_a, **_k: FakeModelResponse(dict(ARTICLE)))
    response = client.post("/api/admin/blogs/generate", json={"publish": publish}, headers=auth)
    assert response.status_code == 200, response.json
    assert response.json["item"]["title"] == ARTICLE["title"] and response.json["item"]["status"] == status
