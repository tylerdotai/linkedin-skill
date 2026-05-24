"""Engagement capabilities: like and comment on LinkedIn posts."""

from __future__ import annotations

import logging

from ..core.client import LinkedInClient
from ..core.errors import SessionExpiredError
from ..core.session import SessionHealth
from ..core.vault import Vault

logger = logging.getLogger(__name__)


def like(post_urn: str, client: LinkedInClient | None = None, vault: Vault | None = None) -> dict[str, bool]:
    """Like a LinkedIn post.

    Args:
        post_urn: The URN of the post to like (e.g., "urn:li:activity:123456789").
        client: Optional LinkedInClient instance. If not provided, creates one.
        vault: Optional Vault instance. If not provided, creates one.

    Returns:
        dict with "success" boolean.

    Raises:
        SessionExpiredError: If session is invalid.
    """
    if client is None:
        client = LinkedInClient()
    if vault is None:
        vault = Vault()

    session_health = SessionHealth(vault, client._http)
    session_health.ensure_valid()

    payload = {"threadUrn": post_urn}
    response = client.post("/voyager/api/voyagerSocialActions/likes", json=payload)

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) while liking post")

    success = response.status_code in (200, 201)
    return {"success": success}


def comment(post_urn: str, text: str, client: LinkedInClient | None = None, vault: Vault | None = None) -> dict[str, str]:
    """Comment on a LinkedIn post.

    Args:
        post_urn: The URN of the post to comment on.
        text: The comment text.
        client: Optional LinkedInClient instance. If not provided, creates one.
        vault: Optional Vault instance. If not provided, creates one.

    Returns:
        dict with "comment_urn" string.

    Raises:
        SessionExpiredError: If session is invalid.
    """
    if client is None:
        client = LinkedInClient()
    if vault is None:
        vault = Vault()

    session_health = SessionHealth(vault, client._http)
    session_health.ensure_valid()

    payload = {
        "threadUrn": post_urn,
        "commentaryV2": {"text": text},
    }
    response = client.post("/voyager/api/voyagerSocialActions/comments", json=payload)

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) while commenting")

    response.raise_for_status()
    data = response.json()

    comment_urn = data.get("id", "")
    return {"comment_urn": comment_urn}