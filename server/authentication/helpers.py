from django.conf import settings
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken


def _issue_jwt_pair(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ── Account lockout ────────────────────────────────────────────────────────────

def _lockout_key(username: str) -> str:
    return f"login_attempts:{username}"


def _is_locked_out(username: str) -> bool:
    return cache.get(_lockout_key(username), 0) >= getattr(settings, "LOGIN_MAX_ATTEMPTS", 5)


def _record_failed_attempt(username: str) -> None:
    key = _lockout_key(username)
    timeout = getattr(settings, "LOGIN_LOCKOUT_SECONDS", 900)
    try:
        cache.incr(key)  # does NOT reset TTL — window anchors to first failure
    except ValueError:
        cache.set(key, 1, timeout=timeout)


def _reset_attempts(username: str) -> None:
    cache.delete(_lockout_key(username))


# ── Cookie helpers ─────────────────────────────────────────────────────────────

def _set_auth_cookies(response, tokens: dict) -> None:
    """Attach access_token + refresh_token (httpOnly) and logged_in (JS-readable)."""
    from datetime import timedelta
    secure = getattr(settings, "JWT_COOKIE_SECURE", False)
    samesite = getattr(settings, "JWT_COOKIE_SAMESITE", "Strict")
    jwt_settings = settings.SIMPLE_JWT
    access_max_age = int(jwt_settings.get("ACCESS_TOKEN_LIFETIME", timedelta(hours=1)).total_seconds())
    refresh_max_age = int(jwt_settings.get("REFRESH_TOKEN_LIFETIME", timedelta(days=7)).total_seconds())

    response.set_cookie(
        settings.JWT_COOKIE_ACCESS_NAME,
        tokens["access"],
        max_age=access_max_age,
        httponly=True,
        secure=secure,
        samesite=samesite,
    )
    response.set_cookie(
        settings.JWT_COOKIE_REFRESH_NAME,
        tokens["refresh"],
        max_age=refresh_max_age,
        httponly=True,
        secure=secure,
        samesite=samesite,
    )
    # Non-httpOnly flag so JS can detect login state
    response.set_cookie(
        settings.JWT_COOKIE_LOGGED_IN_NAME,
        "true",
        max_age=refresh_max_age,
        httponly=False,
        secure=secure,
        samesite=samesite,
    )


def _clear_auth_cookies(response) -> None:
    """Delete all three auth cookies."""
    for name in (
        settings.JWT_COOKIE_ACCESS_NAME,
        settings.JWT_COOKIE_REFRESH_NAME,
        settings.JWT_COOKIE_LOGGED_IN_NAME,
    ):
        response.delete_cookie(name)
