from __future__ import annotations

import httpx

from .flaresolverr import FlareSolverr
from .vault import Vault
from .errors import SessionExpiredError


def normalize_csrf(jessionid: str) -> str:
    return f"ajax:{jessionid}"


class SessionHealth:
    def __init__(self, vault: Vault, client: httpx.Client) -> None:
        self._vault = vault
        self._client = client

    @property
    def headers(self) -> dict[str, str]:
        try:
            cookies = self._vault.load()
        except FileNotFoundError:
            cookies = {}
        jsessionid = cookies.get("JSESSIONID", "")

        return {
            "csrf-token": normalize_csrf(jsessionid),
            "x-restli-protocol-version": "2.0.0",
            "accept": "application/vnd.linkedin.normalized+json+2.1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-li-track": '{"clientVersion":"1.13.20241212.00.00","mpVersion":"1.13.20241212.00.00","osName":"Windows","deviceType":"desktop","themeName":"linkedin","countryCode":"US","actor":"","entityUrn":"urn:li:member:0"}',
            "x-li-lang": "en_US",
        }

    def check(self) -> dict[str, bool | int | str]:
        try:
            cookies = self._vault.load()
        except FileNotFoundError:
            return {"ok": False, "status": 0, "message": "No vault file found"}

        li_at = cookies.get("li_at", "")
        jsessionid = cookies.get("JSESSIONID", "").strip('"')

        flaresolverr_cookies = [
            {"name": "li_at", "value": li_at, "domain": ".linkedin.com", "path": "/"},
            {"name": "JSESSIONID", "value": jsessionid, "domain": ".linkedin.com", "path": "/"},
        ]

        flare = FlareSolverr()
        response = flare.request(
            "GET",
            "https://www.linkedin.com/voyager/api/me",
            cookies=flaresolverr_cookies,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "csrf-token": normalize_csrf(jsessionid),
                "JSESSIONID": jsessionid,
                "x-restli-protocol-version": "2.0.0",
                "accept": "application/vnd.linkedin.normalized+json+2.1",
                "x-li-track": '{"clientVersion":"1.13.20241212.00.00","mpVersion":"1.13.20241212.00.00","osName":"Windows","deviceType":"desktop","themeName":"linkedin","countryCode":"US","actor":"","entityUrn":"urn:li:member:0"}',
                "x-li-lang": "en_US",
            },
        )
        return {
            "ok": response.status_code == 200,
            "status": response.status_code,
            "message": "Session is valid" if response.status_code == 200 else f"Unexpected status: {response.status_code}",
        }

    def ensure_valid(self) -> None:
        result = self.check()
        if not result["ok"]:
            raise SessionExpiredError(result["message"])