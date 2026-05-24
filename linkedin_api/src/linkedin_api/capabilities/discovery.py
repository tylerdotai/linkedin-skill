"""Discovery and search capabilities."""

from __future__ import annotations

import logging
from typing import Any

from ..core.client import LinkedInClient
from ..core.errors import SessionExpiredError
from ..core.session import SessionHealth
from ..core.vault import Vault

logger = logging.getLogger(__name__)


def search_people(
    query: str,
    limit: int,
    client: LinkedInClient,
    vault: Vault,
) -> list[dict[str, str]]:
    """Search for people on LinkedIn.

    Args:
        query: Search query string.
        limit: Maximum number of results to return.
        client: Authenticated LinkedIn client.
        vault: Vault instance for session headers.

    Returns:
        List of dicts with "name", "headline", "profile_url" only (Metis scope lock).

    Raises:
        SessionExpiredError: If session is invalid.
    """
    session = SessionHealth(vault, client._http)
    session.ensure_valid()

    from urllib.parse import quote
    encoded_query = quote(query)

    response = client.get(f"/voyager/api/search/blended?type=people&q={encoded_query}&count={limit}")

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) during people search")

    response.raise_for_status()

    data = response.json()
    elements = data.get("data", {}).get("elements", [])

    results = []
    for element in elements[:limit]:
        # Extract person data from the search result structure
        person = element.get("person", {})
        name = (
            person.get("fullName")
            or person.get("firstName", "") + " " + person.get("lastName", "")
        ).strip()

        headline = person.get("headline", "")
        entity_urn = person.get("entityUrn", "")

        # Construct profile URL from URN
        profile_url = ""
        if entity_urn and "urn:li:member:" in entity_urn:
            member_id = entity_urn.split("urn:li:member:")[-1]
            profile_url = f"https://www.linkedin.com/in/{member_id}"

        results.append({
            "name": name,
            "headline": headline,
            "profile_url": profile_url,
        })

    return results


def get_profile(
    profile_urn_or_url: str,
    client: LinkedInClient,
    vault: Vault,
) -> dict[str, Any]:
    """Get a LinkedIn profile by URN or profile URL.

    Args:
        profile_urn_or_url: Profile URN (e.g., "urn:li:member:123456") or profile URL.
        client: Authenticated LinkedIn client.
        vault: Vault instance for session headers.

    Returns:
        Dict with "headline", "about", "experience", "education".

    Raises:
        SessionExpiredError: If session is invalid.
    """
    session = SessionHealth(vault, client._http)
    session.ensure_valid()

    from urllib.parse import quote

    # Determine if this is a URN or URL
    if profile_urn_or_url.startswith("urn:li:member:"):
        urn_suffix = profile_urn_or_url.split("urn:li:member:")[-1]
        response = client.get(f"/voyager/api/profile/{urn_suffix}")
    else:
        # Assume it's a profile URL, extract the public identifier
        encoded_url = quote(profile_urn_or_url)
        response = client.get(f"/voyager/api/profile?url={encoded_url}")

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) during profile fetch")

    response.raise_for_status()

    data = response.json()

    # Extract profile fields
    result: dict[str, Any] = {
        "headline": data.get("headline", ""),
        "about": data.get("about", "") or data.get("summary", ""),
    }

    # Experience
    positions = data.get("positions", {}).get("elements", [])
    experience = []
    for pos in positions:
        experience.append({
            "title": pos.get("title", ""),
            "company": pos.get("companyName", "") or pos.get("company", {}).get("name", ""),
            "location": pos.get("locationName", ""),
            "date_range": pos.get("dateRange", {}),
        })
    result["experience"] = experience

    # Education
    education = data.get("education", {}).get("elements", [])
    edu_list = []
    for edu in education:
        edu_list.append({
            "school": edu.get("schoolName", ""),
            "degree": edu.get("degreeName", ""),
            "field": edu.get("fieldOfStudy", ""),
        })
    result["education"] = edu_list

    return result