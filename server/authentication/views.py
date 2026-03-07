import logging

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .helpers import _issue_jwt_pair
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
            return Response(
                {
                    "message": "User registered successfully",
                    "user": UserSerializer(user).data,
                    "tokens": tokens,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"error": "Registration failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data["username"],
                password=serializer.validated_data["password"],
            )

            if user:
                log_event(AuditLog.LOGIN_SUCCESS, request=request, user_id=user.id)
                tokens = _issue_jwt_pair(user)
                return Response(
                    {
                        "message": "Login successful",
                        "user": UserSerializer(user).data,
                        "tokens": tokens,
                    }
                )

            log_event(AuditLog.LOGIN_FAILED, request=request, user_id=None)
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {"error": "Login failed", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
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
        # Blacklist the refresh token
        try:
            RefreshToken(request.data.get("refresh")).blacklist()
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
        return Response({"message": "Logged out successfully"})

    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["delete"])
    def delete_account(self, request):
        user = request.user
        user_id = user.id
        try:
            RefreshToken(request.data.get("refresh")).blacklist()
        except Exception as e:
            logger.warning("Failed to blacklist refresh token on account delete: %s", e)
        log_event(AuditLog.ACCOUNT_DELETE, request=request, user_id=user_id)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
