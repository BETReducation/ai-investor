"""Validates the main app's Flask session cookie without running Flask itself.

Reuses flask.sessions.SecureCookieSessionInterface's own serializer (same
salt/signer Flask uses internally) so a cookie minted by the main app is
readable here as long as SECRET_KEY matches on both services. That's a
manual deployment step, not something this module can enforce — see
realtime/README.md.
"""

import os

from flask.sessions import SecureCookieSessionInterface

SECRET_KEY = os.environ.get("SECRET_KEY", "")


class _StubApp:
    """Just enough of a Flask app's interface for get_signing_serializer() —
    secret_key plus the config keys newer Flask versions also read (fallback
    keys we don't use). No need for a real Flask app instance to get the
    serializer."""

    secret_key = SECRET_KEY
    config = {"SECRET_KEY_FALLBACKS": []}


_serializer = SecureCookieSessionInterface().get_signing_serializer(_StubApp()) if SECRET_KEY else None


def user_id_from_session_cookie(cookie_value: str | None) -> str | None:
    if not cookie_value or _serializer is None:
        return None
    try:
        data = _serializer.loads(cookie_value)
    except Exception:
        return None
    return data.get("_user_id")
