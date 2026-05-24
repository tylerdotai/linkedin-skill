from __future__ import annotations

import json
import httpx
import respx
import pytest
from pathlib import Path

from linkedin_api.core.vault import Vault


class TestVaultSaveLoad:
    def test_save_and_load_roundtrip(self, vault: Vault, vault_path: str):
        cookies = {"li_at": "li_at_val", "JSESSIONID": "jsessionid_val"}
        vault.save(cookies)
        loaded = vault.load()
        assert loaded["li_at"] == "li_at_val"
        assert loaded["JSESSIONID"] == "jsessionid_val"

    def test_load_raises_on_missing_file(self, vault: Vault):
        from linkedin_api.core.vault import Vault
        v = Vault()
        v.VAULT_FILE = Path("/nonexistent/path/vault.enc")
        v._key = vault._key
        v._aead = vault._aead
        with pytest.raises(FileNotFoundError):
            v.load()

    def test_clear_removes_vault_file(self, vault: Vault, vault_path: str):
        vault.save({"li_at": "x", "JSESSIONID": "y"})
        assert Path(vault_path).exists()
        vault.clear()
        assert not Path(vault_path).exists()

    def test_clear_is_idempotent(self, vault: Vault, vault_path: str):
        vault.clear()
        vault.clear()


class TestVaultEncryption:
    def test_different_keys_produce_different_ciphertext(self, vault_path: str):
        from linkedin_api.core.vault import Vault
        import os

        os.environ["LINKEDIN_VAULT_KEY"] = "key-one"
        v1 = Vault()
        v1.VAULT_FILE = Path(vault_path)

        os.environ["LINKEDIN_VAULT_KEY"] = "key-two"
        v2 = Vault()
        v2.VAULT_FILE = Path(vault_path)

        v1.save({"li_at": "same", "JSESSIONID": "same"})
        with open(vault_path, "rb") as f:
            ct1 = f.read()

        v2.save({"li_at": "same", "JSESSIONID": "same"})
        with open(vault_path, "rb") as f:
            ct2 = f.read()

        assert ct1 != ct2


class TestVaultIsValid:
    def test_is_valid_returns_true_on_200(self, vault: Vault, respx_mock):
        vault.save({"li_at": "valid_token", "JSESSIONID": "valid_session"})
        respx_mock.get("/voyager/api/me").mock(
            return_value=httpx.Response(200, json={"name": "Test User"})
        )
        assert vault.is_valid() is True

    def test_is_valid_returns_false_on_401(self, vault: Vault, respx_mock):
        vault.save({"li_at": "expired_token", "JSESSIONID": "expired_session"})
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(401))
        assert vault.is_valid() is False

    def test_is_valid_returns_false_when_file_missing(self, vault: Vault):
        v = Vault()
        v.VAULT_FILE = Path("/nonexistent/path/vault.enc")
        v._key = vault._key
        v._aead = vault._aead
        assert v.is_valid() is False

    def test_is_valid_returns_false_when_li_at_missing(self, vault: Vault, respx_mock):
        vault.save({"JSESSIONID": "only_session"})
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200))
        assert vault.is_valid() is False

    def test_is_valid_returns_false_when_jsessionid_missing(self, vault: Vault, respx_mock):
        vault.save({"li_at": "only_token"})
        respx_mock.get("/voyager/api/me").mock(return_value=httpx.Response(200))
        assert vault.is_valid() is False

    def test_is_valid_strips_quotes_from_jsessionid(self, vault: Vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": '"quoted_session"'})
        req = respx_mock.get("/voyager/api/me").mock(
            return_value=httpx.Response(200, json={})
        )
        vault.is_valid()
        call = req.calls[0]
        assert "JSESSIONID=quoted_session" in call.request.headers["Cookie"]

    def test_is_valid_returns_false_on_network_error(self, vault: Vault, respx_mock):
        vault.save({"li_at": "token", "JSESSIONID": "session"})
        respx_mock.get("/voyager/api/me").mock(
            side_effect=httpx.RequestError("connection refused")
        )
        assert vault.is_valid() is False