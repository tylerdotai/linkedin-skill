class SessionExpiredError(Exception):
    pass


class AuthError(Exception):
    pass


class MediaSizeError(Exception):
    """Raised when an image exceeds the 200MB upload limit."""

    pass