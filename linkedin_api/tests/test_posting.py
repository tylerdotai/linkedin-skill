from __future__ import annotations

import httpx
import respx
import pytest
from unittest.mock import patch, MagicMock

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient
from linkedin_api.core.errors import SessionExpiredError


class TestPostText:
    def test_post_text_returns_post_id_on_success(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
            rsps.post("/voyager/api/contentCreation/normShares").mock(
                return_value=httpx.Response(201, json={
                    "data": {
                        "metadata": {
                            "content": {
                                "contentUrn": "urn:li:ugcPost:1234567890"
                            }
                        }
                    }
                })
            )
            from linkedin_api.capabilities.posting import post_text
            result = post_text("Test post content")
            assert "post_id" in result
            assert result["post_id"] == "1234567890"

    def test_post_text_returns_post_url(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
            rsps.post("/voyager/api/contentCreation/normShares").mock(
                return_value=httpx.Response(201, json={
                    "data": {
                        "metadata": {
                            "content": {
                                "contentUrn": "urn:li:ugcPost:999888777"
                            }
                        }
                    }
                })
            )
            from linkedin_api.capabilities.posting import post_text
            result = post_text("Another test post")
            assert "post_url" in result
            assert "999888777" in result["post_url"]

    def test_post_text_raises_on_401(self, vault):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(401))
            from linkedin_api.capabilities.posting import post_text
            with pytest.raises(SessionExpiredError):
                post_text("This should fail")

    def test_post_text_raises_on_http_error(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
            rsps.post("/voyager/api/contentCreation/normShares").mock(
                return_value=httpx.Response(500)
            )
            from linkedin_api.capabilities.posting import post_text
            with pytest.raises(httpx.HTTPStatusError):
                post_text("This should raise")


class TestPostWithImage:
    def test_post_with_image_falls_back_to_text_when_no_image_path(self, vault):
        from linkedin_api.capabilities.posting import post_with_image
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
            rsps.post("/voyager/api/contentCreation/normShares").mock(
                return_value=httpx.Response(201, json={
                    "data": {
                        "metadata": {
                            "entityUrn": "urn:li:ugcPost:111222333"
                        }
                    }
                })
            )
            client = LinkedInClient()
            client._vault = vault
            result = post_with_image("Text only post", None, client, vault)
            assert "post_id" in result
            client.close()

    def test_post_with_image_raises_on_upload_failure(self, vault, tmp_path):
        from linkedin_api.capabilities.posting import post_with_image
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        fake_image = tmp_path / "fake.jpg"
        fake_image.write_bytes(b"fake")
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
            rsps.post("/voyager/api/voyagerMediaUploadMetadata").mock(
                return_value=httpx.Response(200, json={
                    "value": {"uploadUrl": "https://upload.example.com", "mediaArtifact": ""}
                })
            )
            rsps.put("https://upload.example.com").mock(
                return_value=httpx.Response(200)
            )
            client = LinkedInClient()
            client._vault = vault
            with pytest.raises(ValueError, match="Could not extract media URN"):
                post_with_image("Post with image", str(fake_image), client, vault)
            client.close()

    def test_post_with_image_returns_post_id_on_success(self, vault, tmp_path):
        from linkedin_api.capabilities.posting import post_with_image
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        fake_image = tmp_path / "test.jpg"
        fake_image.write_bytes(b"fake image data")
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
            rsps.post("/voyager/api/voyagerMediaUploadMetadata").mock(
                return_value=httpx.Response(200, json={
                    "value": {
                        "uploadUrl": "https://media.linkedin.com/upload-endpoint",
                        "mediaArtifact": "urn:li:fsMediaArtifact:555666777"
                    }
                })
            )
            rsps.put("https://media.linkedin.com/upload-endpoint").mock(
                return_value=httpx.Response(200)
            )
            rsps.post("/voyager/api/contentCreation/normShares").mock(
                return_value=httpx.Response(201, json={
                    "data": {
                        "metadata": {
                            "content": {"contentUrn": "urn:li:ugcPost:123123123"}
                        }
                    }
                })
            )
            client = LinkedInClient()
            client._vault = vault
            result = post_with_image("Check out this image", str(fake_image), client, vault)
            assert "post_id" in result
            client.close()
