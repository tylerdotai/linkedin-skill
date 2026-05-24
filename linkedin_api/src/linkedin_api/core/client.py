"""HTTP client for LinkedIn API with automatic retry, header injection, and sanitized logging."""

from __future__ import annotations

import logging
import time
import re
from typing import Any

import httpx

from .errors import SessionExpiredError
from .session import SessionHealth
from .vault import Vault


class LinkedInServerError(Exception):
    pass


class LinkedInClient:
    BASE_URL = "https://www.linkedin.com"
    RETRY_DELAYS_429 = (30, 60, 120)
    RETRY_DELAY_500 = 10
    MAX_LOG_BODY_LENGTH = 200

    def __init__(self) -> None:
        self._vault = Vault()
        self._http = httpx.Client(
            base_url=self.BASE_URL,
            timeout=30.0,
            follow_redirects=True,
        )
        self._session_health = SessionHealth(self._vault, self._http)
        self._logger = logging.getLogger(__name__)

    def _headers(self) -> dict[str, str]:
        return self._session_health.headers

    def _cookies(self) -> httpx.Cookies:
        cookies = httpx.Cookies()
        try:
            vault_cookies = self._vault.load()
        except FileNotFoundError:
            return cookies

        li_at = vault_cookies.get("li_at", "")
        jsessionid = vault_cookies.get("JSESSIONID", "").strip('"')

        if li_at:
            cookies.set("li_at", li_at, domain=".linkedin.com", path="/")
        if jsessionid:
            cookies.set("JSESSIONID", jsessionid, domain=".linkedin.com", path="/")

        return cookies

    def _sanitize_log(self, text: str) -> str:
        text = re.sub(r'li_at=[^;\s]*', 'li_at=SANITIZED', text)
        text = re.sub(r'JSESSIONID=[^;\s]*', 'JSESSIONID=SANITIZED', text)
        return re.sub(r'Authorization:[^\n]*', 'Authorization: SANITIZED', text)

    def _truncate_body(self, body: str | None) -> str:
        if not body:
            return ""
        if len(body) > self.MAX_LOG_BODY_LENGTH:
            return body[:self.MAX_LOG_BODY_LENGTH] + "... [truncated]"
        return body

    def _log_response(self, method: str, path: str, response: httpx.Response) -> None:
        self._logger.debug(
            "LinkedIn API response: %s %s -> %d | headers: %s | body: %s",
            method,
            path,
            response.status_code,
            self._sanitize_log(str(response.headers)),
            self._truncate_body(response.text),
        )

    def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        headers = self._headers()
        if extra_headers:
            headers.update(extra_headers)
        cookies = self._cookies()

        for attempt, delay in enumerate(self.RETRY_DELAYS_429):
            response = self._http.request(method, path, headers=headers, cookies=cookies, json=json, data=data)
            self._log_response(method, path, response)

            if response.status_code == 401:
                raise SessionExpiredError("LinkedIn session expired (401)")

            if response.status_code != 429:
                return response

            self._logger.warning("Rate limited (429). Retrying in %ds (attempt %d).", delay, attempt + 1)
            time.sleep(delay)

        response = self._http.request(method, path, headers=headers, cookies=cookies, json=json, data=data)
        self._log_response(method, path, response)

        if response.status_code == 429:
            raise LinkedInServerError("Rate limited (429) after all retries")

        if response.status_code == 500:
            self._logger.warning("Got 500. Retrying in %ds.", self.RETRY_DELAY_500)
            time.sleep(self.RETRY_DELAY_500)
            response = self._http.request(method, path, headers=headers, cookies=cookies, json=json, data=data)
            self._log_response(method, path, response)
            if response.status_code == 500:
                raise LinkedInServerError("Got 500 after retry")

        return response

    def get(self, path: str) -> httpx.Response:
        return self._request_with_retry("GET", path)

    def post(self, path: str, json: dict[str, Any] | None = None) -> httpx.Response:
        return self._request_with_retry("POST", path, json=json)

    def put(self, path: str, data: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> httpx.Response:
        return self._request_with_retry("PUT", path, data=data, extra_headers=headers)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "LinkedInClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()