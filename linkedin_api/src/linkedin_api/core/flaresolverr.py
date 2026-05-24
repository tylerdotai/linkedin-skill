from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .vault import Vault


class FlareSolverrError(Exception):
    pass


class FlareLinkedInError(Exception):
    """Raised when LinkedIn API call via FlareSolverr fails."""
    pass


class FlareSolverr:
    BASE_URL = "http://localhost:8191"

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        payload = {
            "cmd": "request.get" if method.upper() == "GET" else "request.post",
            "url": url,
            "maxTimeout": 60000,
        }

        if "cookies" in kwargs:
            payload["cookies"] = kwargs.pop("cookies")
        if "headers" in kwargs:
            payload["headers"] = kwargs.pop("headers")
        if "postData" in kwargs:
            payload["postData"] = kwargs.pop("postData")

        response = httpx.post(
            f"{self.BASE_URL}/v1",
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            solution = data.get("solution", {})
            error_msg = solution.get("error", data.get("message", "Unknown FlareSolverr error"))
            raise FlareSolverrError(f"FlareSolverr returned status={data.get('status')}: {error_msg}")

        solution = data["solution"]

        class FlareSolverrResponse:
            def __init__(self, status_code: int, text: str, headers: dict):
                self.status_code = status_code
                self.text = text
                self.headers = headers

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"HTTP {self.status_code}",
                        request=None,
                        response=self,
                    )

        return FlareSolverrResponse(
            status_code=solution.get("status", 200),
            text=solution.get("response", ""),
            headers=solution.get("headers", {}),
        )


def normalize_csrf(jsessionid: str) -> str:
    return f"ajax:{jsessionid}"


class FlareLinkedInClient:
    """Routes LinkedIn API calls through FlareSolverr proxy.

    FlareSolverr runs a browser with proper cookie context that LinkedIn's API accepts.
    Direct HTTP requests fail because LinkedIn's API returns HTML (login page) even with
    valid cookies when they're not in a proper browser context.
    """

    BASE_URL = "https://www.linkedin.com"
    _logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        self._vault = Vault()
        self._flare = FlareSolverr()

    def _is_html_response(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower().strip()
        return text_lower.startswith("<!doctype") or text_lower.startswith("<html") or "<html" in text_lower

    def _is_login_page(self, text: str) -> bool:
        if not text:
            return False
        text_lower = text.lower()
        login_indicators = ["sign in", "login", "password", "session_key", "session_password"]
        return any(indicator in text_lower for indicator in login_indicators)

    def _cookies(self) -> list[dict[str, str]]:
        try:
            vault_cookies = self._vault.load()
        except FileNotFoundError:
            return []

        li_at = vault_cookies.get("li_at", "")
        jsessionid = vault_cookies.get("JSESSIONID", "").strip('"')

        cookies = []
        if li_at:
            cookies.append({"name": "li_at", "value": li_at, "domain": ".linkedin.com", "path": "/"})
        if jsessionid:
            cookies.append({"name": "JSESSIONID", "value": jsessionid, "domain": ".linkedin.com", "path": "/"})
        return cookies

    def _headers(self, jsessionid: str) -> dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "csrf-token": normalize_csrf(jsessionid),
            "JSESSIONID": jsessionid,
            "x-restli-protocol-version": "2.0.0",
            "accept": "application/vnd.linkedin.normalized+json+2.1",
            "x-li-track": '{"clientVersion":"1.13.20241212.00.00","mpVersion":"1.13.20241212.00.00","osName":"Windows","deviceType":"desktop","themeName":"linkedin","countryCode":"US","actor":"","entityUrn":"urn:li:member:0"}',
            "x-li-lang": "en_US",
        }

    def get(self, path: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}{path}"

        try:
            vault_cookies = self._vault.load()
        except FileNotFoundError:
            raise FlareLinkedInError("No vault file found. Cannot authenticate.")

        jsessionid = vault_cookies.get("JSESSIONID", "").strip('"')
        cookies = self._cookies()
        headers = self._headers(jsessionid)

        response = self._flare.request(
            "GET",
            url,
            cookies=cookies,
            headers=headers,
        )

        if response.status_code != 200:
            raise FlareLinkedInError(
                f"LinkedIn API GET {path} returned {response.status_code}: {response.text[:500]}"
            )

        if self._is_html_response(response.text):
            self._logger.error("FlareLinkedInClient.get(%s) received HTML login page instead of JSON", path)
            if self._is_login_page(response.text):
                raise FlareLinkedInError(
                    f"Session invalid: LinkedIn returned login page for {path}. "
                    "Cookies may be expired or FlareSolverr browser session is not authenticated. "
                    "Re-authenticate via 'linkedin-skill auth'."
                )
            raise FlareLinkedInError(
                f"LinkedIn API GET {path} returned HTML instead of JSON. "
                "Session may be invalid."
            )

        return json.loads(response.text)

    def post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.BASE_URL}{path}"

        try:
            vault_cookies = self._vault.load()
        except FileNotFoundError:
            raise FlareLinkedInError("No vault file found. Cannot authenticate.")

        jsessionid = vault_cookies.get("JSESSIONID", "").strip('"')
        cookies = self._cookies()
        headers = self._headers(jsessionid)

        response = self._flare.request(
            "POST",
            url,
            cookies=cookies,
            headers=headers,
            postData=json.dumps(data),
        )

        if response.status_code != 200:
            raise FlareLinkedInError(
                f"LinkedIn API POST {path} returned {response.status_code}: {response.text[:500]}"
            )

        if self._is_html_response(response.text):
            self._logger.error("FlareLinkedInClient.post(%s) received HTML login page instead of JSON", path)
            if self._is_login_page(response.text):
                raise FlareLinkedInError(
                    f"Session invalid: LinkedIn returned login page for {path}. "
                    "Cookies may be expired or FlareSolverr browser session is not authenticated. "
                    "Re-authenticate via 'linkedin-skill auth'."
                )
            raise FlareLinkedInError(
                f"LinkedIn API POST {path} returned HTML instead of JSON. "
                "Session may be invalid."
            )

        return json.loads(response.text)