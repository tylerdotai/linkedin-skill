"""Pytest configuration and shared fixtures for LinkedIn API tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import httpx
import pytest
import respx

os.environ["LINKEDIN_VAULT_KEY"] = "test-vault-key-for-testing-12345"

from linkedin_api.core.vault import Vault
from linkedin_api.core.client import LinkedInClient
from linkedin_api.core.session import SessionHealth
from linkedin_api.core.errors import SessionExpiredError


@pytest.fixture
def vault_path(tmp_path: Path) -> str:
    return str(tmp_path / "vault.enc")


@pytest.fixture
def vault(vault_path: str) -> Generator[Vault, None, None]:
    v = Vault()
    v.VAULT_FILE = Path(vault_path)
    yield v
    if Path(vault_path).exists():
        Path(vault_path).unlink()


@pytest.fixture
def mock_vault():
    return MagicMock(spec=Vault)


SAMPLE_COOKIES = {
    "li_at": "test-li_at-value-abc123",
    "JSESSIONID": "test-jsessionid-value-xyz789",
}

SAMPLE_COOKIES_QUOTED = {
    "li_at": "test-li_at-value-abc123",
    "JSESSIONID": '"test-jsessionid-value-xyz789"',
}


@pytest.fixture
def respx_mock():
    with respx.mock(assert_all_called=False, base_url="https://www.linkedin.com") as rsps:
        yield rsps


@pytest.fixture
def client(vault: Vault, respx_mock) -> Generator[LinkedInClient, None, None]:
    with respx.mock(base_url="https://www.linkedin.com", assert_all_called=False):
        c = LinkedInClient()
        c._vault = vault
        yield c
        c.close()


@pytest.fixture
def session_health(vault: Vault, mock_httpx_client: httpx.Client) -> SessionHealth:
    return SessionHealth(vault, mock_httpx_client)


@pytest.fixture
def mock_httpx_client() -> httpx.Client:
    return httpx.Client(base_url="https://www.linkedin.com")


def mock_200(path: str = "/voyager/api/me", json_data: dict | None = None) -> respx.Route:
    return respx.get(path).mock(return_value=httpx.Response(200, json=json_data or {}))


def mock_401(path: str = "/voyager/api/me") -> respx.Route:
    return respx.get(path).mock(return_value=httpx.Response(401))


def mock_403(path: str = "/voyager/api/me") -> respx.Route:
    return respx.get(path).mock(return_value=httpx.Response(403))


def mock_429(path: str = "/voyager/api/me", retries: int = 3) -> list[respx.Route]:
    routes = []
    for _ in range(retries):
        routes.append(respx.get(path).mock(return_value=httpx.Response(429)))
    routes.append(respx.get(path).mock(return_value=httpx.Response(200)))
    return routes


def mock_500(path: str = "/voyager/api/me") -> respx.Route:
    return respx.get(path).mock(return_value=httpx.Response(500))