from __future__ import annotations

import httpx
import respx
import pytest

from linkedin_api.core.session import SessionHealth, normalize_csrf
from linkedin_api.core.errors import SessionExpiredError


class TestNormalizeCsrf:
    def test_appends_ajax_prefix(self):
        assert normalize_csrf("session123") == "ajax:session123"

    def test_no_double_ajax_prefix(self):
        assert normalize_csrf("ajax:already_prefixed") == "ajax:ajax:already_prefixed"


class TestSessionHealthHeaders:
    def test_headers_contain_csrf_token(self, vault, mock_httpx_client, respx_mock):
        vault.save({"li_at": "token_abc", "JSESSIONID": "session_xyz"})
        session = SessionHealth(vault, mock_httpx_client)
        headers = session.headers
        assert "csrf-token" in headers
        assert headers["csrf-token"] == "ajax:session_xyz"

    def test_headers_contain_restli_protocol_version(self, vault, mock_httpx_client, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        session = SessionHealth(vault, mock_httpx_client)
        assert session.headers["x-restli-protocol-version"] == "2.0.0"

    def test_headers_contain_accept_media_type(self, vault, mock_httpx_client, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        session = SessionHealth(vault, mock_httpx_client)
        assert "accept" in session.headers
        assert "linkedin" in session.headers["accept"].lower()

    def test_headers_contain_user_agent(self, vault, mock_httpx_client, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        session = SessionHealth(vault, mock_httpx_client)
        assert "user-agent" in session.headers
        assert "Mozilla" in session.headers["user-agent"]

    def test_headers_handle_missing_vault_file(self, vault, mock_httpx_client, respx_mock):
        from pathlib import Path
        v = vault.__class__()
        v.VAULT_FILE = Path("/nonexistent/vault.enc")
        v._key = vault._key
        v._aead = vault._aead
        session = SessionHealth(v, mock_httpx_client)
        headers = session.headers
        assert "csrf-token" in headers


class TestEnsureValid:
    def test_ensure_valid_passes_on_200(self, vault, respx_mock):
        vault.save({"li_at": "valid_token", "JSESSIONID": "valid_session"})
        client = httpx.Client(base_url="https://www.linkedin.com")
        session = SessionHealth(vault, client)
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200, json={}))
        session.ensure_valid()
        client.close()

    def test_ensure_valid_raises_on_401(self, vault, respx_mock):
        vault.save({"li_at": "expired_token", "JSESSIONID": "expired_session"})
        client = httpx.Client(base_url="https://www.linkedin.com")
        session = SessionHealth(vault, client)
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(401))
        with pytest.raises(SessionExpiredError):
            session.ensure_valid()
        client.close()