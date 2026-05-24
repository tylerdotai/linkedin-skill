from __future__ import annotations

import httpx
import respx
import pytest

from linkedin_api.core.auth import normalize_csrf, check_session


class TestNormalizeCsrf:
    def test_wraps_raw_jsessionid_in_ajax_prefix(self):
        raw = "abc123xyz"
        assert normalize_csrf(raw) == "ajax:abc123xyz"

    def test_strips_surrounding_quotes_from_jsessionid(self):
        raw = '"some-session-value"'
        assert normalize_csrf(raw) == "ajax:some-session-value"

    def test_strips_quotes_and_wraps(self):
        raw = '"jsessionid-with-quotes"'
        result = normalize_csrf(raw)
        assert result == "ajax:jsessionid-with-quotes"
        assert not result.startswith('"')
        assert not result.endswith('"')


class TestCheckSession:
    def test_returns_valid_when_200(self, vault, vault_path):
        vault.save({"li_at": "token_val", "JSESSIONID": "session_val"})
        from unittest.mock import patch, MagicMock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"firstName": "Tyler"}}
        with patch.object(httpx.Client, "get", return_value=mock_response) as mock_get:
            result = check_session(vault_path=str(vault.VAULT_FILE))
            assert result["valid"] is True
            assert result["reason"] == "Session is valid"

    def test_returns_invalid_when_401(self, vault, vault_path):
        vault.save({"li_at": "expired_token", "JSESSIONID": "expired_session"})
        from unittest.mock import patch, MagicMock
        mock_response = MagicMock()
        mock_response.status_code = 401
        with patch.object(httpx.Client, "get", return_value=mock_response):
            result = check_session(vault_path=str(vault.VAULT_FILE))
            assert result["valid"] is False
            assert "401" in result["reason"]

    def test_returns_invalid_when_vault_missing(self, vault_path):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            fake_path = f.name
        result = check_session(vault_path=fake_path)
        assert result["valid"] is False
        assert "Vault" in result["reason"]

    def test_returns_invalid_when_cookies_empty(self, vault, vault_path):
        from pathlib import Path
        empty_vault_path = str(Path(vault_path).parent / "empty_vault.enc")
        v = vault.__class__()
        v.VAULT_FILE = Path(empty_vault_path)
        v.save({})
        result = check_session(vault_path=empty_vault_path)
        assert result["valid"] is False

    def test_returns_invalid_when_li_at_missing(self, vault, vault_path):
        from pathlib import Path
        no_li_at_path = str(Path(vault_path).parent / "no_li_at.enc")
        v = vault.__class__()
        v.VAULT_FILE = Path(no_li_at_path)
        v.save({"JSESSIONID": "some_session"})
        result = check_session(vault_path=no_li_at_path)
        assert result["valid"] is False

    def test_returns_invalid_on_network_error(self, vault, vault_path):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        from unittest.mock import patch, MagicMock
        with patch.object(httpx.Client, "get", side_effect=httpx.ConnectError("connection refused")):
            result = check_session(vault_path=str(vault.VAULT_FILE))
            assert result["valid"] is False
            assert "Network error" in result["reason"]
