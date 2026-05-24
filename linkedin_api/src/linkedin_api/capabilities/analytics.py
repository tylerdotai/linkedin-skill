from __future__ import annotations

import logging

from ..core.client import LinkedInClient
from ..core.errors import SessionExpiredError
from ..core.session import SessionHealth
from ..core.vault import Vault

logger = logging.getLogger(__name__)


def get_post_insights(post_urn: str, client: LinkedInClient | None = None, vault: Vault | None = None) -> dict[str, int]:
    """Fetch engagement insights for a specific LinkedIn post.

    Args:
        post_urn: The post URN (e.g., " urn:li:activity:123456").
        client: Optional LinkedInClient instance. If not provided, creates one.
        vault: Optional Vault instance. If not provided, creates one.

    Returns:
        Dict with views, likes, comments, shares.

    Raises:
        SessionExpiredError: If session is invalid.
    """
    if client is None:
        client = LinkedInClient()
    if vault is None:
        vault = Vault()

    session_health = SessionHealth(vault, client._http)
    session_health.ensure_valid()

    path = f"/voyager/api/socialFeed/socialFeedUpdates/{post_urn}/social有权用的"
    response = client.get(path)

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) fetching post insights")

    response.raise_for_status()
    data = response.json()

    views = 0
    likes = 0
    comments = 0
    shares = 0

    try:
        view_count = data.get("data", {}).get("viewCount", 0) or 0
        like_count = data.get("data", {}).get("likeCount", 0) or 0
        comment_count = data.get("data", {}).get("commentCount", 0) or 0
        share_count = data.get("data", {}).get("shareCount", 0) or 0

        if isinstance(view_count, int):
            views = view_count
        if isinstance(like_count, int):
            likes = like_count
        if isinstance(comment_count, int):
            comments = comment_count
        if isinstance(share_count, int):
            shares = share_count
    except Exception as e:
        logger.warning("Failed to parse post insights response: %s", e)

    return {
        "views": views,
        "likes": likes,
        "comments": comments,
        "shares": shares,
    }