from __future__ import annotations

import httpx
import respx
import pytest

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient
from linkedin_api.core.errors import SessionExpiredError


class TestGetMyFeed:
    def test_get_my_feed_returns_list(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.get("/voyager/api/feed/updates/me").mock(
            return_value=httpx.Response(200, json={
                "data": {
                    "elements": [
                        {
                            "id": "urn:li:activity:111222333",
                            "commentary": {"text": "My first post!"},
                            "created": {"time": 1700000000000},
                            "socialCount": {"liked": 42, "comments": 5}
                        }
                    ]
                }
            })
        )
        from linkedin_api.capabilities.feed import get_my_feed
        results = get_my_feed(limit=10, vault=vault)
        assert len(results) == 1
        assert results[0]["post_id"] == "111222333"
        assert results[0]["text"] == "My first post!"
        assert results[0]["likes"] == 42
        assert results[0]["comments"] == 5
        client.close()

    def test_get_my_feed_raises_on_401(self, vault, respx_mock):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(401))
        from linkedin_api.capabilities.feed import get_my_feed
        with pytest.raises(SessionExpiredError):
            get_my_feed(limit=10, vault=vault)
        client.close()

    def test_get_my_feed_handles_empty_feed(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(
            return_value=httpx.Response(200, json={})
        )
        respx_mock.get("/voyager/api/feed/updates/me").mock(
            return_value=httpx.Response(200, json={"data": {"elements": []}})
        )
        from linkedin_api.capabilities.feed import get_my_feed
        results = get_my_feed(limit=10, vault=vault)
        assert results == []
        client.close()