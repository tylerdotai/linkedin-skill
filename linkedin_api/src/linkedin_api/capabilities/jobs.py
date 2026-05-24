from __future__ import annotations

import logging

from ..core.client import LinkedInClient
from ..core.errors import SessionExpiredError
from ..core.session import SessionHealth
from ..core.vault import Vault

logger = logging.getLogger(__name__)


def search_jobs(
    query: str,
    location: str | None,
    client: LinkedInClient | None = None,
    vault: Vault | None = None,
) -> list[dict[str, str]]:
    """Search for LinkedIn jobs.

    Args:
        query: Job search keywords.
        location: Optional location filter.
        client: Optional LinkedInClient instance. If not provided, creates one.
        vault: Optional Vault instance. If not provided, creates one.

    Returns:
        List of job listings with title, company, location.

    Raises:
        SessionExpiredError: If session is invalid.
    """
    if client is None:
        client = LinkedInClient()
    if vault is None:
        vault = Vault()

    session_health = SessionHealth(vault, client._http)
    session_health.ensure_valid()

    path = f"/voyager/api/jobs/jobSearch?keywords={query}"
    if location:
        path += f"&location={location}"

    response = client.get(path)

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) searching jobs")

    response.raise_for_status()
    data = response.json()

    jobs = []
    try:
        elements = data.get("data", {}).get("elements", []) or []
        for job in elements:
            title = job.get("title", "") or ""
            company = job.get("company", {}).get("name", "") if isinstance(job.get("company"), dict) else ""
            job_location = job.get("location", "") or ""
            jobs.append({
                "title": str(title),
                "company": str(company),
                "location": str(job_location),
            })
    except Exception as e:
        logger.warning("Failed to parse job search response: %s", e)

    return jobs


def bookmark_job(
    job_id: str,
    client: LinkedInClient | None = None,
    vault: Vault | None = None,
) -> dict[str, bool]:
    """Bookmark a LinkedIn job.

    Args:
        job_id: The job ID to bookmark.
        client: Optional LinkedInClient instance. If not provided, creates one.
        vault: Optional Vault instance. If not provided, creates one.

    Returns:
        Dict with success boolean.

    Raises:
        SessionExpiredError: If session is invalid.
    """
    if client is None:
        client = LinkedInClient()
    if vault is None:
        vault = Vault()

    session_health = SessionHealth(vault, client._http)
    session_health.ensure_valid()

    response = client.put(f"/voyager/api/jobs/jobSearch/{job_id}/bookmark")

    if response.status_code == 401:
        raise SessionExpiredError("Session expired (401) bookmarking job")

    return {"success": response.status_code in (200, 201)}