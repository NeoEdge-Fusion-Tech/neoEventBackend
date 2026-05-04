"""
accounts/password_serializers.py
Password-related serializers kept separate from the core auth serializers
for maintainability.
"""

from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from ..models import User


# ─────────────────────────────────────────────────────────────────────────────
# Forgot-password flow (unauthenticated)
# ─────────────────────────────────────────────────────────────────────────────

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Step 1 — Accept the user's email and trigger the reset email.

    Deliberately vague on validation: we always return 200 even if the email
    is not registered, to prevent user enumeration attacks.
    """

    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Step 2 — Accept uid + token (from the reset link) plus the new password.
    Validates the token and sets the new password.
    """

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, data: dict) -> dict:
        # ── Decode UID ────────────────────────────────────────────
        try:
            uid = force_str(urlsafe_base64_decode(data["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError(
                {"uid": "Reset link is invalid or has already been used."}
            )

        # ── Validate token ────────────────────────────────────────
        generator = PasswordResetTokenGenerator()
        if not generator.check_token(user, data["token"]):
            raise serializers.ValidationError(
                {"token": "Reset link is invalid or has expired. Please request a new one."}
            )

        # ── Password match ────────────────────────────────────────
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )

        # ── Django password validators (strength, common passwords…) ──
        try:
            validate_password(data["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})

        # Stash the resolved user so the view doesn't need to decode again
        data["_user"] = user
        return data

    def save(self) -> User:
        user: User = self.validated_data["_user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


# ─────────────────────────────────────────────────────────────────────────────
# Change-password flow (authenticated)
# ─────────────────────────────────────────────────────────────────────────────

class PasswordChangeSerializer(serializers.Serializer):
    """
    Authenticated users can change their own password by providing the current
    password alongside the new one.
    """

    current_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate_current_password(self, value: str) -> str:
        user: User = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data: dict) -> dict:
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )

        user: User = self.context["request"].user

        if data["new_password"] == data["current_password"]:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from your current password."}
            )

        try:
            validate_password(data["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})

        return data

    def save(self) -> User:
        user: User = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
        
        