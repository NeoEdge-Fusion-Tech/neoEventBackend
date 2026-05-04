# serializers/auth.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from ..models import User, VendorProfile, EventOwnerProfile, AttendeeProfile
from .user import UserSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data

class BaseRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "password", "password_confirm", "first_name", "last_name")

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        validate_password(attrs["password"])
        return attrs


class VendorRegisterSerializer(BaseRegisterSerializer):
    vendor_subtype = serializers.ChoiceField(choices=VendorProfile.VendorSubtype.choices)
    service_title = serializers.CharField(help_text="Brief title describing the your specialization.")
    service_areas = serializers.CharField(help_text="Comma-separated list of locations served.")

    class Meta(BaseRegisterSerializer.Meta):
        fields = BaseRegisterSerializer.Meta.fields + (
            "phone_number", "vendor_subtype", "service_title", "service_areas",
        )
    def create(self, validated_data):

        validated_data.pop("password_confirm")

        vendor_subtype = validated_data.pop("vendor_subtype")
        service_title = validated_data.pop("service_title")
        service_areas = validated_data.pop("service_areas")

        user = User.objects.create_user(
            **validated_data,
            role=User.Role.VENDOR,
            onboarding_status=User.OnboardingStatus.PENDING_APPROVAL,
        )

        VendorProfile.objects.create(
            user=user,
            subtype=vendor_subtype,
            service_title=service_title,
            service_areas=service_areas,
        )
        return user


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "role",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        role = validated_data.pop("role")
        user = User.objects.create_user(
            **validated_data,
            role=role,
            onboarding_status=User.OnboardingStatus.PENDING_EMAIL,
            is_active=False,
        )

        return user

class AttendeeRegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = AttendeeProfile
        fields = (
            "full_name",
            "email",
            "phone_number",
            "reference_image",
        )

    def create(self, validated_data):
        return AttendeeProfile.objects.create(**validated_data)
        
        