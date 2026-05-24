from __future__ import annotations

import httpx
import respx
import pytest

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient
from linkedin_api.core.errors import SessionExpiredError


class TestSendConnectionRequest:
    def test_send_connection_request_with_note(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/relConnectionCreationV2").mock(
            return_value=httpx.Response(201, json={"requestId": "req_12345"})
        )
        from linkedin_api.capabilities.network import send_connection_request
        result = send_connection_request(
            "urn:li:member:555666",
            note="Let's connect!",
            client=client,
            vault=vault
        )
        assert "request_id" in result
        client.close()

    def test_send_connection_request_without_note(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/voyagerNetworkMemberFollowing/v2/follow").mock(
            return_value=httpx.Response(201, json={"requestId": "req_67890"})
        )
        from linkedin_api.capabilities.network import send_connection_request
        result = send_connection_request(
            "urn:li:member:555666",
            note=None,
            client=client,
            vault=vault
        )
        assert "request_id" in result
        client.close()

    def test_send_connection_request_raises_on_401(self, vault, respx_mock):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(401))
        from linkedin_api.capabilities.network import send_connection_request
        with pytest.raises(SessionExpiredError):
            send_connection_request("urn:li:member:555666", "Hi!", client=client, vault=vault)
        client.close()


class TestAcceptConnection:
    def test_accept_connection_returns_success(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.put("/voyager/api/voyagerNetworkMemberFollowing/request/req_abc").mock(
            return_value=httpx.Response(200)
        )
        from linkedin_api.capabilities.network import accept_connection
        result = accept_connection("req_abc", client=client, vault=vault)
        assert result["success"] is True
        client.close()


class TestRejectConnection:
    def test_reject_connection_returns_success(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.put("/voyager/api/voyagerNetworkMemberFollowing/request/req_xyz").mock(
            return_value=httpx.Response(200)
        )
        from linkedin_api.capabilities.network import reject_connection
        result = reject_connection("req_xyz", client=client, vault=vault)
        assert result["success"] is True
        client.close()