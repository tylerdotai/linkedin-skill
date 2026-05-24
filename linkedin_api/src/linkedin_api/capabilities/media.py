from __future__ import annotations

import mimetypes
from pathlib import Path

from ..core.client import LinkedInClient
from ..core.errors import MediaSizeError

MAX_IMAGE_SIZE = 200 * 1024 * 1024


def upload_image(image_path: str | Path, client: LinkedInClient) -> dict[str, str]:
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    file_size = path.stat().st_size
    if file_size > MAX_IMAGE_SIZE:
        raise MediaSizeError(
            f"Image size ({file_size / (1024*1024):.1f}MB) exceeds the 200MB limit"
        )

    filename = path.name
    mimetypes.guess_type(str(path))[0] or "image/jpeg"

    metadata_payload = {
        "recipe": "feedshare-image",
        "fileSize": file_size,
        "filename": filename,
    }

    init_resp = client.post(
        "/voyager/api/voyagerMediaUploadMetadata?action=upload",
        json=metadata_payload,
    )
    init_resp.raise_for_status()
    init_data = init_resp.json()

    upload_url = init_data.get("value", {}).get("uploadUrl")
    if not upload_url:
        raise ValueError("No uploadUrl in init response")

    with open(path, "rb") as f:
        binary_data = f.read()

    put_resp = client.put(
        upload_url,
        data=binary_data,
        headers={"Content-Type": "application/octet-stream"},
    )
    put_resp.raise_for_status()

    media_urn = init_data.get("value", {}).get("mediaArtifact", "")

    if not media_urn:
        location = put_resp.headers.get("location", "")
        if location:
            media_urn = location.split("/")[-1]

    if not media_urn:
        raise ValueError("Could not extract media URN from upload response")

    media_url = f"https://media.linkedin.com/digitalmediaUrn={media_urn}"

    return {
        "media_urn": media_urn,
        "media_url": media_url,
    }