"""Messaging capabilities: send DMs and reply to conversation threads."""

from __future__ import annotations

import logging

from ..core.client import LinkedInClient
from ..core.errors import SessionExpiredError
from ..core.session import SessionHealth
from ..core.vault import Vault

logger = logging.getLogger(__name__)


def send_dm(profile_urn: str, message: str, client: LinkedInClient | None = None, vault: Vault | None = None) -> dict[str, str]:
    """Send a direct message to a LinkedIn profile.

    Args:
        profile_urn: The URN of the recipient profile.
        message: The message text to send.
        client: Optional LinkedInClient instance. If not provided, creates one.
        vault: Optional Vault instance. If not provided, creates one.

    Returns:
        dict with "message_id" string.

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
        "recipients": [profile_urn],
        "body": message,
    }
    response = client.post("/voyager/api/messaging/v2/conversations", json=payload)

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) while sending DM")

    response.raise_for_status()
    data = response.json()

    message_id = data.get("id", "")
    return {"message_id": message_id}


def reply_to_thread(thread_id: str, message: str, client: LinkedInClient | None = None, vault: Vault | None = None) -> dict[str, str]:
    """Reply to an existing messaging conversation thread.

    Args:
        thread_id: The conversation thread ID.
        message: The reply message text.
        client: Optional LinkedInClient instance. If not provided, creates one.
        vault: Optional Vault instance. If not provided, creates one.

    Returns:
        dict with "message_id" string.

    Raises:
        SessionExpiredError: If session is invalid.
    """
    if client is None:
        client = LinkedInClient()
    if vault is None:
        vault = Vault()

    session_health = SessionHealth(vault, client._http)
    session_health.ensure_valid()

    payload = {"message": message}
    response = client.post(f"/voyager/api/messaging/v2/conversations/{thread_id}/events", json=payload)

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) while replying to thread")

    response.raise_for_status()
    data = response.json()

    message_id = data.get("id", "")
    return {"message_id": message_id}