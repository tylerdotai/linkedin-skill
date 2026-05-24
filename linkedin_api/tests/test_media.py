from __future__ import annotations

import httpx
import respx
import pytest
from pathlib import Path

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient
from linkedin_api.core.errors import MediaSizeError


class TestUploadImage:
    def test_upload_image_raises_on_missing_file(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        from linkedin_api.capabilities.media import upload_image
        with pytest.raises(FileNotFoundError):
            upload_image("/nonexistent/image.jpg", client)
        client.close()

    def test_upload_image_raises_on_oversized_file(self, vault, respx_mock, tmp_path):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        large_file = tmp_path / "large.jpg"
        large_file.write_bytes(b"x" * (201 * 1024 * 1024))
        client = LinkedInClient()
        client._vault = vault
        from linkedin_api.capabilities.media import upload_image
        with pytest.raises(MediaSizeError):
            upload_image(str(large_file), client)
        client.close()

    def test_upload_image_success(self, vault, respx_mock, tmp_path):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data" * 100)
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/voyagerMediaUploadMetadata").mock(
            return_value=httpx.Response(200, json={
                "value": {
                    "uploadUrl": "https://media.linkedin.com/upload-endpoint",
                    "mediaArtifact": "urn:li:fsMediaArtifact:12345"
                }
            })
        )
        respx_mock.put("https://media.linkedin.com/upload-endpoint").mock(
            return_value=httpx.Response(200)
        )
        from linkedin_api.capabilities.media import upload_image
        result = upload_image(str(test_image), client)
        assert "media_urn" in result
        assert "media_url" in result
        assert result["media_urn"] == "urn:li:fsMediaArtifact:12345"
        client.close()