import json
from typing import Optional

import requests
from flask import current_app
from slugify import slugify

from . import site_service


class AIUnavailable(Exception):
    """No model is configured. Nothing is generated: a canned article published as if
    it were written for the site is worse than no article."""


def generate_blog_post(topic: Optional[str] = None) -> dict:
    # Use the live site identity so the daily blog follows a rebrand (new
    # industry/audience), not the original env defaults.
    site = site_service.effective()
    topic = topic or site["industry"]
    api_key = current_app.config["DEEPSEEK_API_KEY"]
    if not api_key:
        raise AIUnavailable("DEEPSEEK_API_KEY is not set")

    prompt = {
        "industry": topic,
        "audience": site["audience"],
        "region": site["region"],
        "requirements": [
            "Return valid JSON only.",
            "Write a useful evergreen blog post.",
            "Optimize for SEO and generative engine optimization.",
            "Include local/geographic relevance where natural.",
            "Avoid fake statistics and unverifiable claims.",
        ],
        "schema": {
            "title": "string",
            "slug": "string",
            "excerpt": "string",
            "body_markdown": "string",
            "tags": ["string"],
            "meta_title": "string",
            "meta_description": "string",
        },
    }
    response = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": current_app.config["DEEPSEEK_MODEL"],
            "messages": [
                {"role": "system", "content": "You are an expert editorial SEO/GEO content strategist."},
                {"role": "user", "content": json.dumps(prompt)},
            ],
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    post = json.loads(content)
    post["slug"] = slugify(post.get("slug") or post["title"])
    return post
