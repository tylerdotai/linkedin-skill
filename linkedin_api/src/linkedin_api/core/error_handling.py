"""Error handling utilities for LinkedIn API client."""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from .errors import (
    SessionExpiredError,
    AuthError,
    MediaSizeError,
)

logger = logging.getLogger(__name__)

SENSITIVE_HEADERS = {"li_at", "jsessionid", "csrf_token", "authorization"}


class LinkedInError(Exception):
    """Base exception for all LinkedIn API errors."""
    pass


class AccountCompromisedError(LinkedInError):
    """Raised when LinkedIn returns 403 — potential account compromise."""
    pass


class RateLimitError(LinkedInError):
    """Raised when LinkedIn returns 429 — rate limit exceeded."""

    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limited, retry after {retry_after}s")


class LinkedInServerError(LinkedInError):
    pass


class NetworkTimeoutError(LinkedInError):
    pass


class CSRFMismatchError(LinkedInError):
    pass


def sanitize_log_headers(headers: dict) -> dict:
    """Remove sensitive values from headers before logging.

    Args:
        headers: Response headers dict

    Returns:
        Sanitized dict with sensitive values redacted
    """
    if not headers:
        return {}

    sanitized = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if key_lower in SENSITIVE_HEADERS:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    return sanitized


def log_error(
    endpoint: str,
    status: Optional[int],
    response_body: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """Log an error with sanitized information.

    Args:
        endpoint: API endpoint that failed
        status: HTTP status code (or None for network errors)
        response_body: Response body (cookies stripped)
        details: Additional context dict
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    log_data = {
        "timestamp": timestamp,
        "endpoint": endpoint,
        "status": status,
        "response_body": response_body,
        "details": details or {},
    }

    if response_body and "li_at" in response_body.lower():
        import re
        log_data["response_body"] = re.sub(
            r"li_at=[^&\s]+", "li_at=[REDACTED]", response_body, flags=re.IGNORECASE
        )
    if response_body and "JSESSIONID" in response_body.upper():
        import re
        log_data["response_body"] = re.sub(
            r"JSESSIONID=[^&\s]+", "JSESSIONID=[REDACTED]", response_body, flags=re.IGNORECASE
        )

    logger.error("LinkedIn API error: %s", log_data)


def exponential_backoff(delay: float, max_retries: int) -> float:
    """Calculate exponential backoff delay.

    Args:
        delay: Base delay in seconds
        max_retries: Current retry attempt number (1-based)

    Returns:
        Delay in seconds for this retry attempt
    """
    return delay * (2 ** (max_retries - 1))


def handle_http_error(status: int, response_body: Optional[str], endpoint: str) -> Exception:
    """Map HTTP status code to appropriate exception and log.

    Args:
        status: HTTP status code
        response_body: Response body for logging
        endpoint: API endpoint

    Returns:
        Appropriate exception instance

    Raises:
        SessionExpiredError: On 401 — do not retry, re-auth required
        AccountCompromisedError: On 403 — pause operations
        RateLimitError: On 429 — backoff and retry
        LinkedInServerError: On 500 — retry once
    """
    log_error(endpoint, status, response_body)

    if status == 401:
        return SessionExpiredError("Session expired, re-auth required")
    if status == 403:
        return AccountCompromisedError("Account access forbidden — possible compromise")
    if status == 429:
        return RateLimitError()
    if status >= 500:
        return LinkedInServerError(f"LinkedIn server error: {status}")

    return AuthError(f"Unexpected error: {status}")


def retry_with_backoff(
    func,
    max_attempts: int = 3,
    base_delay: float = 5.0,
    max_delay: float = 30.0,
    endpoint: str = "unknown",
) -> tuple:
    """Retry a function with exponential backoff on network errors.

    Args:
        func: Callable to retry
        max_attempts: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        endpoint: API endpoint for logging

    Returns:
        Tuple of (success: bool, result/error)

    Raises:
        SessionExpiredError: Propagates immediately on 401
        AccountCompromisedError: Propagates immediately on 403
        RateLimitError: Raises for caller to handle with their own backoff
        LinkedInServerError: Retries once with 10s delay
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return (True, func())
        except SessionExpiredError:
            raise
        except AccountCompromisedError:
            raise
        except RateLimitError:
            raise
        except LinkedInServerError:
            if attempt == 1:
                time.sleep(10)
                continue
            raise
        except (ConnectionError, TimeoutError, NetworkTimeoutError) as e:
            last_error = e
            if attempt < max_attempts:
                delay = min(exponential_backoff(base_delay, attempt), max_delay)
                log_error(endpoint, None, details={"retry": attempt, "delay": delay, "error": str(e)})
                time.sleep(delay)
            continue
        except CSRFMismatchError:
            raise

    return (False, last_error)


def handle_csrf_error(endpoint: str, func) -> tuple:
    """Handle CSRF mismatch by regenerating token and retrying once.

    Args:
        endpoint: API endpoint for logging
        func: Callable to retry after CSRF regeneration

    Returns:
        Tuple of (success: bool, result/error)
    """
    log_error(endpoint, None, details={"csrf_retry": True})
    try:
        return (True, func())
    except CSRFMismatchError:
        log_error(endpoint, None, details={"csrf_retry_failed": True})
        return (False, CSRFMismatchError("CSRF regeneration failed"))