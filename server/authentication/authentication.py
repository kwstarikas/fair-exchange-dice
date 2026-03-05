from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


class BlacklistingJWTAuthentication(JWTAuthentication):
    """
    Extends JWTAuthentication to also reject access tokens whose JTI
    has been explicitly blacklisted (e.g. on logout).

    By default simplejwt only blacklists refresh tokens. This class makes
    the blacklist check apply to access tokens too.
    """

    def get_validated_token(self, raw_token):
        validated_token = super().get_validated_token(raw_token)

        jti = validated_token.get('jti')
        if jti and BlacklistedToken.objects.filter(token__jti=jti).exists():
            raise AuthenticationFailed(
                'Token has been invalidated. Please log in again.',
                code='token_blacklisted',
            )

        return validated_token
