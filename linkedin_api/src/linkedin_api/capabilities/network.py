"""Network and connection management capabilities."""

from __future__ import annotations

import logging
from typing import Any

from ..core.client import LinkedInClient
from ..core.errors import SessionExpiredError
from ..core.session import SessionHealth
from ..core.vault import Vault

logger = logging.getLogger(__name__)


def send_connection_request(
    profile_urn: str,
    note: str | None,
    client: LinkedInClient,
    vault: Vault,
) -> dict[str, str]:
    """Send a connection request to a LinkedIn profile.

    Args:
        profile_urn: The LinkedIn profile URN (e.g., "urn:li:member:123456").
        note: Optional note to include with the connection request.
        client: Authenticated LinkedIn client.
        vault: Vault instance for session headers.

    Returns:
        Dict with "request_id" on success.

    Raises:
        SessionExpiredError: If session is invalid.
    """
    session = SessionHealth(vault, client._http)
    session.ensure_valid()
    headers = session.headers.copy()

    if note:
        # Connection request with note
        payload: dict[str, Any] = {
            "message": note,
            "entityUrn": profile_urn,
        }
        response = client.post("/voyager/api/relConnectionCreationV2", json=payload)
    else:
        # Connection request without note
        payload = {
            "type": "CONNECT",
            "entityUrn": profile_urn,
        }
        response = client.post("/voyager/api/voyagerNetworkMemberFollowing/v2/follow", json=payload)

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) during connection request")

    response.raise_for_status()

    data = response.json()
    request_id = (
        data.get("requestId")
        or data.get("request_id")
        or data.get("data", {}).get("requestId")
    )

    return {"request_id": request_id}


def accept_connection(request_urn: str, client: LinkedInClient, vault: Vault) -> dict[str, bool]:
    """Accept a connection request.

    Args:
        request_urn: The connection request URN.
        client: Authenticated LinkedIn client.
        vault: Vault instance for session headers.

    Returns:
        Dict with "success" boolean.

    Raises:
        SessionExpiredError: If session is invalid.
    """
    session = SessionHealth(vault, client._http)
    session.ensure_valid()

    payload = {"action": "ACCEPT"}
    response = client.put(f"/voyager/api/voyagerNetworkMemberFollowing/request/{request_urn}", data=payload)

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) during accept connection")

    response.raise_for_status()

    return {"success": response.status_code in (200, 201, 204)}


def reject_connection(request_urn: str, client: LinkedInClient, vault: Vault) -> dict[str, bool]:
    """Reject a connection request.

    Args:
        request_urn: The connection request URN.
        client: Authenticated LinkedIn client.
        vault: Vault instance for session headers.

    Returns:
        Dict with "success" boolean.

    Raises:
        SessionExpiredError: If session is invalid.
    """
    session = SessionHealth(vault, client._http)
    session.ensure_valid()

    payload = {"action": "REJECT"}
    response = client.put(f"/voyager/api/voyagerNetworkMemberFollowing/request/{request_urn}", data=payload)

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) during reject connection")

    response.raise_for_status()

    return {"success": response.status_code in (200, 201, 204)}