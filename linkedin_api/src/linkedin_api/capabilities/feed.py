from __future__ import annotations

import logging

import httpx

from ..core.client import LinkedInClient
from ..core.errors import SessionExpiredError
from ..core.session import SessionHealth
from ..core.vault import Vault

logger = logging.getLogger(__name__)


def get_my_feed(limit: int, client: LinkedInClient | None = None, vault: Vault | None = None) -> list[dict[str, str | int]]:
    """Fetch the authenticated user's LinkedIn feed.

    Args:
        limit: Maximum number of feed updates to return.
        client: Optional LinkedInClient instance. If not provided, creates one.
        vault: Optional Vault instance. If not provided, creates one.

    Returns:
        List of dicts with post_id, text, timestamp, likes, comments.

    Raises:
        SessionExpiredError: If session is invalid.
    """
    if client is None:
        client = LinkedInClient()
    if vault is None:
        vault = Vault()

    session_health = SessionHealth(vault, client._http)
    session_health.ensure_valid()

    response = client.get(f"/voyager/api/feed/updates/me?count={limit}")

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) fetching feed")

    response.raise_for_status()
    data = response.json()

    feed_updates = data.get("data", {}).get("elements", [])
    parsed = []

    for update in feed_updates:
        try:
            post_id = update.get("id", "") or update.get("entityUrn", "") or ""
            if "urn:li:activity:" in post_id:
                post_id = post_id.split(":")[-1]
            elif "urn:li:ugcPost:" in post_id:
                post_id = post_id.split(":")[-1]

            text = ""
            content = update.get("content", {})
            if content:
                text = content.get("text", "") or content.get("commentary", "") or ""

            if not text:
                sub_content = update.get("commentary", {})
                if isinstance(sub_content, dict):
                    text = sub_content.get("text", "") or ""

            timestamp = update.get("created", {}).get("time", "") or ""
            if timestamp:
                import datetime
                timestamp = datetime.datetime.fromtimestamp(timestamp / 1000).isoformat()

            social_counts = update.get("socialCount", {}) or {}
            likes = social_counts.get("liked", 0) or 0
            comments = social_counts.get("comments", 0) or 0

            if not isinstance(likes, int):
                likes = 0
            if not isinstance(comments, int):
                comments = 0

            parsed.append({
                "post_id": str(post_id),
                "text": str(text),
                "timestamp": str(timestamp),
                "likes": likes,
                "comments": comments,
            })
        except Exception as e:
            logger.warning("Failed to parse feed update: %s", e)
            continue

    return parsed