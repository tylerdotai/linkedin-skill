"""Encrypted cookie vault for LinkedIn API session storage."""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class VaultKeyError(Exception):
    """Raised when LINKEDIN_VAULT_KEY environment variable is missing."""

    pass


class Vault:
    """AES-256-GCM encrypted storage for LinkedIn session cookies.

    Stores: li_at, JSESSIONID, expiration timestamps
    Path: ~/.config/linkedin_api/vault.enc
    """

    VAULT_DIR = Path.home() / ".config" / "linkedin_api"
    VAULT_FILE = VAULT_DIR / "vault.enc"
    VALIDATION_URL = "https://www.linkedin.com/voyager/api/me"

    def __init__(self):
        self._key = self._get_key()
        self._aead = AESGCM(self._key)

    def _get_key(self) -> bytes:
        """Derive 32-byte AES-256 key from LINKEDIN_VAULT_KEY env var."""
        env_key = os.environ.get("LINKEDIN_VAULT_KEY")
        if not env_key:
            raise VaultKeyError(
                "LINKEDIN_VAULT_KEY environment variable is not set. "
                "Please set it to a secure key value."
            )
        # Use SHA-256 to derive a consistent 32-byte key from the env string
        import hashlib
        return hashlib.sha256(env_key.encode()).digest()

    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt data using AES-256-GCM. Returns nonce + ciphertext + tag."""
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = self._aead.encrypt(nonce, data, None)
        return nonce + ciphertext

    def _decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt AES-256-GCM encrypted data. Returns plaintext."""
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        return self._aead.decrypt(nonce, ciphertext, None)

    def save(self, cookies: dict) -> None:
        """Encrypt and save cookies to vault file.

        Args:
            cookies: Dict containing 'li_at', 'JSESSIONID', and optionally 'expires_at'
        """
        self.VAULT_DIR.mkdir(parents=True, exist_ok=True)

        plaintext = json.dumps(cookies).encode("utf-8")
        encrypted = self._encrypt(plaintext)

        with open(self.VAULT_FILE, "wb") as f:
            f.write(encrypted)

    def load(self) -> dict:
        """Decrypt and load cookies from vault file.

        Returns:
            Dict with 'li_at', 'JSESSIONID', 'expires_at'

        Raises:
            FileNotFoundError: If vault file does not exist
        """
        if not self.VAULT_FILE.exists():
            raise FileNotFoundError(f"Vault file not found: {self.VAULT_FILE}")

        with open(self.VAULT_FILE, "rb") as f:
            encrypted = f.read()

        plaintext = self._decrypt(encrypted)
        return json.loads(plaintext.decode("utf-8"))

    def is_valid(self) -> bool:
        """Validate session by calling LinkedIn /voyager/api/me endpoint.

        Returns:
            True if session is valid (200 response), False if expired (401)
        """
        try:
            cookies = self.load()
        except FileNotFoundError:
            return False

        li_at = cookies.get("li_at")
        jsessionid = cookies.get("JSESSIONID")

        if not li_at or not jsessionid:
            return False

        # Normalize JSESSIONID - strip surrounding quotes if present
        jsessionid = jsessionid.strip('"')

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; LinkedInBot/1.0)",
            "csrf-token": jsessionid,
            "JSESSIONID": jsessionid,
            "Cookie": f"li_at={li_at}; JSESSIONID={jsessionid}",
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.VALIDATION_URL, headers=headers)
                return response.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    def clear(self) -> None:
        """Remove the vault file."""
        if self.VAULT_FILE.exists():
            self.VAULT_FILE.unlink()