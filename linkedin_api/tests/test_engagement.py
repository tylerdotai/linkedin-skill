from __future__ import annotations

import httpx
import respx
import pytest

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient
from linkedin_api.core.errors import SessionExpiredError


class TestLike:
    def test_like_returns_success_on_200(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/voyagerSocialActions/likes").mock(
            return_value=httpx.Response(200)
        )
        from linkedin_api.capabilities.engagement import like
        result = like("urn:li:activity:12345", client=client, vault=vault)
        assert result["success"] is True
        client.close()

    def test_like_returns_success_on_201(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/voyagerSocialActions/likes").mock(
            return_value=httpx.Response(201)
        )
        from linkedin_api.capabilities.engagement import like
        result = like("urn:li:activity:12345", client=client, vault=vault)
        assert result["success"] is True
        client.close()

    def test_like_returns_false_on_other_status(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/voyagerSocialActions/likes").mock(
            return_value=httpx.Response(204)
        )
        from linkedin_api.capabilities.engagement import like
        result = like("urn:li:activity:12345", client=client, vault=vault)
        assert result["success"] is False
        client.close()

    def test_like_raises_on_401(self, vault, respx_mock):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(401))
        from linkedin_api.capabilities.engagement import like
        with pytest.raises(SessionExpiredError):
            like("urn:li:activity:12345", client=client, vault=vault)
        client.close()


class TestComment:
    def test_comment_returns_comment_urn(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/voyagerSocialActions/comments").mock(
            return_value=httpx.Response(201, json={"id": "urn:li:comment:12345"})
        )
        from linkedin_api.capabilities.engagement import comment
        result = comment("urn:li:activity:67890", "Great post!", client=client, vault=vault)
        assert "comment_urn" in result
        client.close()

    def test_comment_raises_on_401(self, vault, respx_mock):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(401))
        from linkedin_api.capabilities.engagement import comment
        with pytest.raises(SessionExpiredError):
            comment("urn:li:activity:67890", "Great post!", client=client, vault=vault)
        client.close()

    def test_comment_raises_on_http_error(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/voyagerSocialActions/comments").mock(
            return_value=httpx.Response(500)
        )
        from linkedin_api.capabilities.engagement import comment
        with pytest.raises(httpx.HTTPStatusError):
            comment("urn:li:activity:67890", "Great post!", client=client, vault=vault)
        client.close()