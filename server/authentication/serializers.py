import re

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

_NAME_RE = re.compile(r"^[a-zA-Z\s-]+$")
_USERNAME_RE = re.compile(r"^[a-z0-9]+$")


def _validate_name(value):
    if not _NAME_RE.match(value):
        raise serializers.ValidationError(
            "Name must contain only letters, hyphens, or spaces"
        )
    return value


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    first_name = serializers.CharField(required=True, min_length=2, max_length=50)
    last_name = serializers.CharField(required=True, min_length=2, max_length=50)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name")

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters")
        if len(value) > 15:
            raise serializers.ValidationError(
                "Username must be less than 15 characters"
            )
        if not _USERNAME_RE.match(value):
            raise serializers.ValidationError(
                "Username must contain only lowercase letters and numbers"
            )
        return value

    def validate_first_name(self, value):
        return _validate_name(value)

    def validate_last_name(self, value):
        return _validate_name(value)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details (read-only)."""

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "date_joined")
        read_only_fields = fields
