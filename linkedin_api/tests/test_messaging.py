from __future__ import annotations

import httpx
import respx
import pytest

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient
from linkedin_api.core.errors import SessionExpiredError


class TestSendDm:
    def test_send_dm_returns_message_id_on_success(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/messaging/v2/conversations").mock(
            return_value=httpx.Response(201, json={"id": "msg_12345"})
        )
        from linkedin_api.capabilities.messaging import send_dm
        result = send_dm("urn:li:member:999888", "Hello there!", client=client, vault=vault)
        assert "message_id" in result
        assert result["message_id"] == "msg_12345"
        client.close()

    def test_send_dm_raises_on_401(self, vault, respx_mock):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(401))
        from linkedin_api.capabilities.messaging import send_dm
        with pytest.raises(SessionExpiredError):
            send_dm("urn:li:member:999888", "Hello!", client=client, vault=vault)
        client.close()

    def test_send_dm_raises_on_http_error(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/messaging/v2/conversations").mock(
            return_value=httpx.Response(500)
        )
        from linkedin_api.capabilities.messaging import send_dm
        with pytest.raises(httpx.HTTPStatusError):
            send_dm("urn:li:member:999888", "Hello!", client=client, vault=vault)
        client.close()


class TestReplyToThread:
    def test_reply_to_thread_returns_message_id_on_success(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/messaging/v2/conversations/thread_abc/events").mock(
            return_value=httpx.Response(200, json={"id": "reply_msg_999"})
        )
        from linkedin_api.capabilities.messaging import reply_to_thread
        result = reply_to_thread("thread_abc", "Thanks for your message!", client=client, vault=vault)
        assert "message_id" in result
        assert result["message_id"] == "reply_msg_999"
        client.close()

    def test_reply_to_thread_raises_on_401(self, vault, respx_mock):
        vault.save({"li_at": "expired", "JSESSIONID": "expired"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(401))
        from linkedin_api.capabilities.messaging import reply_to_thread
        with pytest.raises(SessionExpiredError):
            reply_to_thread("thread_abc", "Thanks!", client=client, vault=vault)
        client.close()

    def test_reply_to_thread_raises_on_http_error(self, vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        client = LinkedInClient()
        client._vault = vault
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        respx_mock.post("/voyager/api/messaging/v2/conversations/thread_abc/events").mock(
            return_value=httpx.Response(500)
        )
        from linkedin_api.capabilities.messaging import reply_to_thread
        with pytest.raises(httpx.HTTPStatusError):
            reply_to_thread("thread_abc", "Thanks!", client=client, vault=vault)
        client.close()