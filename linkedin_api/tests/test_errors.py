from __future__ import annotations

import time
import httpx
import respx
import pytest
from unittest.mock import patch, MagicMock

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient, LinkedInServerError
from linkedin_api.core.errors import SessionExpiredError


class Test401Handling:
    def test_session_expired_error_raised_on_401(self, vault):
        vault.save({"li_at": "expired_token", "JSESSIONID": "expired_session"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            client = LinkedInClient()
            client._vault = vault
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(401))
            rsps.post("/voyager/api/voyagerSocialActions/likes").mock(
                return_value=httpx.Response(401)
            )
            from linkedin_api.capabilities.engagement import like
            with pytest.raises(SessionExpiredError):
                like("urn:li:activity:12345", client=client, vault=vault)
            client.close()

    def test_401_raised_in_posting(self, vault):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            client = LinkedInClient()
            client._vault = vault
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(401))
            from linkedin_api.capabilities.posting import post_text
            with pytest.raises(SessionExpiredError):
                post_text("Test post")
            client.close()


class Test403Handling:
    def test_403_raises_http_status_error(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            client = LinkedInClient()
            client._vault = vault
            rsps.get("/voyager/api/me").mock(
                return_value=httpx.Response(200, json={})
            )
            rsps.get("/voyager/api/search/blended").mock(
                return_value=httpx.Response(403)
            )
            from linkedin_api.capabilities.discovery import search_people
            with pytest.raises(httpx.HTTPStatusError):
                search_people("engineer", limit=5, client=client, vault=vault)
            client.close()


class Test429Handling:
    def test_rate_limit_raises_server_error_after_retries(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            client = LinkedInClient()
            client._vault = vault
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(429))
            with patch("time.sleep") as mock_sleep:
                with pytest.raises(LinkedInServerError, match="Rate limited"):
                    client.get("/voyager/api/me")
            client.close()

    def test_rate_limit_retries_then_succeeds(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            client = LinkedInClient()
            client._vault = vault
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(429))
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(429))
            rsps.get("/voyager/api/me").mock(
                return_value=httpx.Response(200, json={"data": {"foo": "bar"}})
            )
            with patch("time.sleep"):
                response = client.get("/voyager/api/me")
                assert response.status_code == 200
            client.close()


class Test500Handling:
    def test_500_retries_once_then_raises(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            client = LinkedInClient()
            client._vault = vault
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(500))
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(500))
            with patch("time.sleep"):
                with pytest.raises(LinkedInServerError, match="500 after retry"):
                    client.get("/voyager/api/me")
            client.close()

    def test_500_succeeds_on_retry(self, vault):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False) as rsps:
            client = LinkedInClient()
            client._vault = vault
            rsps.get("/voyager/api/me").mock(return_value=httpx.Response(500))
            rsps.get("/voyager/api/me").mock(
                return_value=httpx.Response(200, json={"data": {"baz": "qux"}})
            )
            with patch("time.sleep"):
                response = client.get("/voyager/api/me")
                assert response.status_code == 200
            client.close()
