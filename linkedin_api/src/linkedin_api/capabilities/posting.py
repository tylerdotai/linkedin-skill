from __future__ import annotations

import logging
import re
from typing import Any

from ..core.flaresolverr import FlareLinkedInClient, FlareLinkedInError
from ..core.errors import SessionExpiredError

logger = logging.getLogger(__name__)


class ImageUploadError(Exception):
    """Raised when image upload fails."""
    pass


def post_text(text: str) -> dict[str, str]:
    """Post to LinkedIn via FlareSolverr. Returns {"error": "session invalid", ...} on auth failure."""
    client = FlareLinkedInClient()
    try:
        response = client.post(
            "/voyager/api/ugcPosts",
            {
                "author": "urn:li:member:ME",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
                },
            },
        )
    except FlareLinkedInError as e:
        logger.error("FlareLinkedInError during post_text: %s", e)
        return {"error": "session invalid", "message": str(e)}

    post_info = extract_post_info(response)
    post_info["post_url"] = construct_post_url(post_info["post_id"])

    return {
        "post_id": post_info["post_id"],
        "post_url": post_info["post_url"],
    }


def post_with_image(text: str, image_path: str | None) -> dict[str, Any]:
    if image_path is None:
        return post_text(text)

    raise NotImplementedError("Image posting via FlareSolverr is not yet implemented")


def extract_post_info(response_json: dict[str, Any]) -> dict[str, Any]:
    """Extract post ID from LinkedIn API response.

    Tries multiple field paths to extract the post ID.

    Args:
        response_json: Parsed JSON response from LinkedIn API.

    Returns:
        Dict with post_id (str or None) and post_url (str or None).
        Returns None values with a warning log if format is unrecognized.
    """
    # Primary path: data.metadata.content.contentUrn
    try:
        content_urn = (
            response_json.get("data", {})
            .get("metadata", {})
            .get("content", {})
            .get("contentUrn")
        )
        if content_urn:
            post_id = content_urn.split(":")[-1] if ":" in content_urn else content_urn
            return {"post_id": post_id, "post_url": None}
    except (KeyError, TypeError, AttributeError):
        pass

    # Fallback: data.contentUrn
    try:
        content_urn = response_json.get("data", {}).get("contentUrn")
        if content_urn:
            post_id = content_urn.split(":")[-1] if ":" in content_urn else content_urn
            return {"post_id": post_id, "post_url": None}
    except (KeyError, TypeError, AttributeError):
        pass

    # Fallback: data.linkedin.standardizedCreatedActivityURN
    try:
        activity_urn = response_json.get("data", {}).get("linkedin", {}).get("standardizedCreatedActivityURN")
        if activity_urn:
            post_id = activity_urn.split(":")[-1] if ":" in activity_urn else activity_urn
            return {"post_id": post_id, "post_url": None}
    except (KeyError, TypeError, AttributeError):
        pass

    # Fallback: id at top level
    try:
        post_id = response_json.get("id")
        if post_id:
            return {"post_id": post_id, "post_url": None}
    except (KeyError, TypeError):
        pass

    # Fallback: data.id
    try:
        post_id = response_json.get("data", {}).get("id")
        if post_id:
            return {"post_id": post_id, "post_url": None}
    except (KeyError, TypeError):
        pass

    # Fallback: entityUrn pattern (urn:li:ugcPost:XXX)
    try:
        entity_urn = (
            response_json.get("data", {})
            .get("metadata", {})
            .get("entityUrn")
            or response_json.get("data", {})
            .get("entityUrn")
            or response_json.get("entityUrn")
        )
        if entity_urn and "urn:li:ugcPost:" in entity_urn:
            post_id = entity_urn.split("urn:li:ugcPost:")[-1]
            return {"post_id": post_id, "post_url": None}
    except (KeyError, TypeError, AttributeError):
        pass

    # Fallback: regex search for urn:li:activity: pattern in serialized JSON
    try:
        import json
        data_str = json.dumps(response_json)
        match = re.search(r'urn:li:activity:\d+', data_str)
        if match:
            post_id = match.group(0).split(":")[-1]
            return {"post_id": post_id, "post_url": None}
    except (KeyError, TypeError, AttributeError):
        pass

    # Fallback: regex search for urn:li:ugcPost: pattern
    try:
        data_str = json.dumps(response_json)
        match = re.search(r'urn:li:ugcPost:\d+', data_str)
        if match:
            post_id = match.group(0).split("urn:li:ugcPost:")[-1]
            return {"post_id": post_id, "post_url": None}
    except (KeyError, TypeError, AttributeError):
        pass

    # Unknown format - log warning and return None values
    logger.warning(
        "Unable to extract post ID from LinkedIn response. "
        f"Response keys: {list(response_json.keys())}"
    )
    return {"post_id": None, "post_url": None}


def construct_post_url(post_id: str | None) -> str | None:
    """Construct the LinkedIn post URL from a post ID.

    Args:
        post_id: The LinkedIn post ID (URN suffix or full URN).

    Returns:
        Full LinkedIn post URL, or None if post_id is None.
    """
    if post_id is None:
        return None

    # Strip various URN prefixes if present
    for prefix in ["urn:li:activity:", "urn:li:ugcPost:", "urn:li:share:"]:
        if prefix in post_id:
            post_id = post_id.split(prefix)[-1]

    return f"https://www.linkedin.com/feed/update/{post_id}"