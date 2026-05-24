"""Patchright-based LinkedIn authentication — cookie capture and session validation."""

from __future__ import annotations

from patchright.sync_api import sync_playwright

from .errors import AuthError
from .vault import Vault


def normalize_csrf(raw_jsessionid: str) -> str:
    return f"ajax:{raw_jsessionid.strip('"')}"


def authenticate(
    username: str,
    password: str,
    vault_path: str | None = None,
    headless: bool = False,
    two_fa_timeout: float = 120.0,
) -> bool:
    vault_file = vault_path or Vault.VAULT_FILE

    vault = Vault()
    vault.VAULT_FILE = vault_file

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            context = browser.new_context()
            page = context.new_page()

            page.goto("https://www.linkedin.com/login", timeout=30_000)
            page.wait_for_timeout(3000)

            page.evaluate(
                """(data) => {
        const el = document.querySelector('input[name="' + data.key + '"]');
        if (el) {
            el.value = data.val;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }""",
                {"key": "session_key", "val": username},
            )
            page.evaluate(
                """(data) => {
        const el = document.querySelector('input[name="' + data.key + '"]');
        if (el) {
            el.value = data.val;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }""",
                {"key": "session_password", "val": password},
            )
            page.locator('button[type="submit"]').click(force=True, timeout=5000)

            try:
                page.wait_for_selector(
                    'input[aria-label*="verification"]',
                    timeout=two_fa_timeout,
                )
                page.wait_for_url("**/feed/**", timeout=two_fa_timeout)
            except Exception:
                page.wait_for_url("**/feed/**", timeout=30_000)

            cookies = context.cookies()

            li_at = next((c["value"] for c in cookies if c["name"] == "li_at"), None)
            raw_jsessionid = next(
                (c["value"] for c in cookies if c["name"] == "JSESSIONID"), None
            )

            if not li_at:
                raise AuthError("li_at cookie not found after login")
            if not raw_jsessionid:
                raise AuthError("JSESSIONID cookie not found after login")

            vault.save({"li_at": li_at, "JSESSIONID": raw_jsessionid.strip('"').replace("ajax:", "", 1)})
            return True

        except AuthError:
            raise
        except Exception as exc:
            raise AuthError(f"Authentication failed: {exc}") from exc
        finally:
            browser.close()


def check_session(vault_path: str | None = None) -> dict:
    vault = Vault()
    if vault_path:
        vault.VAULT_FILE = vault_path

    if not vault.VAULT_FILE.exists():
        return {"valid": False, "reason": "Vault not found"}

    cookies = vault.load()
    if not cookies:
        return {"valid": False, "reason": "Missing cookies in vault"}

    li_at = cookies.get("li_at")
    jsessionid = cookies.get("JSESSIONID")

    if not li_at or not jsessionid:
        return {"valid": False, "reason": "Missing cookies in vault"}

    return {"valid": True, "reason": "Cookies present, session assumed valid"}