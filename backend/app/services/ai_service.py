import json
from datetime import datetime
from typing import Optional

import requests
from flask import current_app
from slugify import slugify

from . import site_service


def _fallback_post(topic: str) -> dict:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    title = f"{topic.title()} Operating Notes for {today}"
    return {
        "title": title,
        "slug": slugify(title),
        "excerpt": f"A practical daily note for people building in {topic}.",
        "body_markdown": (
            f"# {title}\n\n"
            "A useful daily blog should answer one concrete question, show a small working pattern, "
            "and leave the reader with one action they can take today.\n\n"
            "## Framework\n\n"
            "- Define the audience.\n"
            "- State the problem in plain language.\n"
            "- Offer a repeatable workflow.\n"
            "- Add examples that search engines and AI answer engines can understand.\n\n"
            "## Takeaway\n\n"
            "Publish consistently, keep the API clean, and make every page easy to cite."
        ),
        "tags": [topic, "daily", "seo", "geo"],
        "meta_title": title[:60],
        "meta_description": f"Daily {topic} blog with SEO and GEO structure for modern websites.",
    }


def generate_blog_post(topic: Optional[str] = None) -> dict:
    # Use the live site identity so the daily blog follows a rebrand (new
    # industry/audience), not the original env defaults.
    site = site_service.effective()
    topic = topic or site["industry"]
    api_key = current_app.config["DEEPSEEK_API_KEY"]
    if not api_key:
        return _fallback_post(topic)

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
