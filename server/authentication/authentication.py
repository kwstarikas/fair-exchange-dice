from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


class BlacklistingJWTAuthentication(JWTAuthentication):
    """
    Extends JWTAuthentication to:
    1. Also reject access tokens whose JTI has been explicitly blacklisted (e.g. on logout).
    2. Accept the token from an httpOnly cookie when no Authorization header is present.
       The header path is tried first so existing tests (which use client.credentials())
       continue to work without modification.
    """

    def authenticate(self, request):
        # 1. Try Authorization header first (keeps test compatibility)
        header = self.get_header(request)
        if header is not None:
            raw_token = self.get_raw_token(header)
            if raw_token is not None:
                validated = self.get_validated_token(raw_token)
                return self.get_user(validated), validated

        # 2. Fall back to httpOnly cookie
        cookie_name = getattr(settings, "JWT_COOKIE_ACCESS_NAME", "access_token")
        raw_token = request.COOKIES.get(cookie_name)
        if raw_token is None:
            return None
        validated = self.get_validated_token(raw_token.encode())
        return self.get_user(validated), validated

    def get_validated_token(self, raw_token):
        validated_token = super().get_validated_token(raw_token)

        jti = validated_token.get('jti')
        if jti and BlacklistedToken.objects.filter(token__jti=jti).exists():
            raise AuthenticationFailed(
                'Token has been invalidated. Please log in again.',
                code='token_blacklisted',
            )

        return validated_token
