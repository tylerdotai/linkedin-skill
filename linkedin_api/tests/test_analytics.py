from __future__ import annotations

import httpx
import respx
import pytest

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient
from linkedin_api.core.errors import SessionExpiredError


class TestGetPostInsights:
    def test_get_post_insights_returns_views_likes_comments_shares(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
            rsps.get(respx.router.Resolver()).mock(
                return_value=httpx.Response(200, json={
                    "data": {
                        "viewCount": 1500,
                        "likeCount": 87,
                        "commentCount": 12,
                        "shareCount": 3
                    }
                })
            )
            from linkedin_api.capabilities.analytics import get_post_insights
            result = get_post_insights("urn:li:activity:12345", vault=vault)
            assert result["views"] == 1500
            assert result["likes"] == 87
            assert result["comments"] == 12
            assert result["shares"] == 3
        client.close()

    def test_get_post_insights_raises_on_401(self, vault):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(401))
            from linkedin_api.capabilities.analytics import get_post_insights
            with pytest.raises(SessionExpiredError):
                get_post_insights("urn:li:activity:12345", vault=vault)
        client.close()
