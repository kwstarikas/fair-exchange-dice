import logging

from django.conf import settings
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth.models import User

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .helpers import (
    _issue_jwt_pair,
    _is_locked_out, _record_failed_attempt, _reset_attempts,
    _set_auth_cookies, _clear_auth_cookies,
)
from audit.models import log_event, AuditLog

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.GenericViewSet):
    def get_permissions(self):
        if self.action in ["register", "login"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "register":
            return RegisterSerializer
        elif self.action == "login":
            return LoginSerializer
        return UserSerializer

    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            log_event(AuditLog.REGISTER, request=request, user_id=user.id)
            tokens = _issue_jwt_pair(user)
            response = Response(
                {
                    "message": "User registered successfully",
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
            _set_auth_cookies(response, tokens)
            return response

        return Response(
            {"error": "Registration failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Login failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = serializer.validated_data["username"]

        if _is_locked_out(username):
            log_event(AuditLog.LOGIN_FAILED, request=request, user_id=None)
            return Response(
                {"error": "Account temporarily locked due to too many failed attempts. "
                          "Please try again in 15 minutes."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        user = authenticate(
            username=username,
            password=serializer.validated_data["password"],
        )

        if user:
            _reset_attempts(username)
            log_event(AuditLog.LOGIN_SUCCESS, request=request, user_id=user.id)
            tokens = _issue_jwt_pair(user)
            response = Response(
                {
                    "message": "Login successful",
                    "user": UserSerializer(user).data,
                }
            )
            _set_auth_cookies(response, tokens)
            return response

        _record_failed_attempt(username)
        log_event(AuditLog.LOGIN_FAILED, request=request, user_id=None)
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    @action(detail=False, methods=["post"])
    def logout(self, request):
        """
        Fully invalidate the session by blacklisting both tokens:
        - Refresh token: can no longer be used to obtain new access tokens
        - Access token: immediately rejected on any future request

        POST /api/auth/logout/
        Body: {"refresh": "<refresh_token>"}
        """
        # Blacklist the refresh token (read from cookie, fall back to body for tests)
        refresh_str = request.COOKIES.get(
            getattr(settings, "JWT_COOKIE_REFRESH_NAME", "refresh_token")
        ) or request.data.get("refresh")
        try:
            if refresh_str:
                RefreshToken(refresh_str).blacklist()
        except Exception as e:
            logger.warning("Failed to blacklist refresh token: %s", e)

        # Blacklist the current access token by its JTI
        try:
            from datetime import datetime, timezone as dt_timezone
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken,
            )

            jti = request.auth["jti"]
            outstanding, _ = OutstandingToken.objects.get_or_create(
                jti=jti,
                defaults={
                    "user": request.user,
                    "token": str(request.auth),
                    "created_at": datetime.fromtimestamp(
                        request.auth["iat"], tz=dt_timezone.utc
                    ),
                    "expires_at": datetime.fromtimestamp(
                        request.auth["exp"], tz=dt_timezone.utc
                    ),
                },
            )
            BlacklistedToken.objects.get_or_create(token=outstanding)
        except Exception as e:
            logger.warning("Failed to blacklist access token: %s", e)

        log_event(AuditLog.LOGOUT, request=request, user_id=request.user.id)
        response = Response({"message": "Logged out successfully"})
        _clear_auth_cookies(response)
        return response

    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["delete"])
    def delete_account(self, request):
        user = request.user
        user_id = user.id
        refresh_str = request.COOKIES.get(
            getattr(settings, "JWT_COOKIE_REFRESH_NAME", "refresh_token")
        ) or request.data.get("refresh")
        try:
            if refresh_str:
                RefreshToken(refresh_str).blacklist()
        except Exception as e:
            logger.warning("Failed to blacklist refresh token on account delete: %s", e)
        log_event(AuditLog.ACCOUNT_DELETE, request=request, user_id=user_id)
        user.delete()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        _clear_auth_cookies(response)
        return response


class CookieTokenRefreshView(APIView):
    """
    Token refresh endpoint that reads the refresh token from the httpOnly cookie
    and sets new cookies on the response. Falls back to request body for test
    compatibility (DRF test client sends body, not cookies).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        cookie_name = getattr(settings, "JWT_COOKIE_REFRESH_NAME", "refresh_token")
        refresh_str = request.COOKIES.get(cookie_name) or request.data.get("refresh")

        if not refresh_str:
            return Response(
                {"error": "No refresh token provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_str)
            tokens = {
                "access": str(refresh.access_token),
                "refresh": str(refresh),  # rotated token
            }
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({"message": "Token refreshed", "access": tokens["access"]})
        _set_auth_cookies(response, tokens)
        return response


class UserViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

