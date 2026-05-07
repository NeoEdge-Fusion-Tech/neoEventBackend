# serializers/auth.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from ..models import User, VendorProfile, EventOwnerProfile, AttendeeProfile
from .user import UserSerializer
from django.db import transaction



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    default_error_messages = {
        "no_active_account": "Invalid credentials."
    }

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

    def create(self, validated_data):
        # Remove password_confirm before saving to the model
        validated_data.pop("password_confirm")
        # Use create_user to handle password hashing
        return User.objects.create_user(**validated_data)


class EventOwnerRegisterSerializer(BaseRegisterSerializer):
    class Meta(BaseRegisterSerializer.Meta):
        # We override fields to keep it slim for the Owner signup
        fields = ("username", "email", "phone_number", "password", "password_confirm")

    def create(self, validated_data):
        with transaction.atomic():
            # Set the role internally so it's not a dropdown in Swagger
            validated_data['role'] = User.Role.OWNER
            
            # This calls BaseRegisterSerializer.create()
            user = super().create(validated_data)
            
            # Create the one-to-one profile
            EventOwnerProfile.objects.create(user=user)
            
            return user
        

class VendorRegisterSerializer(BaseRegisterSerializer):
    vendor_subtype = serializers.ChoiceField(choices=VendorProfile.VendorSubtype.choices)

    class Meta(BaseRegisterSerializer.Meta):
        # We explicitly list ONLY what we want. No first_name or last_name here.
        fields = ("username", "email","phone_number", "password", "password_confirm", "vendor_subtype")

    def create(self, validated_data):
        vendor_subtype = validated_data.pop("vendor_subtype")

        with transaction.atomic():
            validated_data['role'] = User.Role.VENDOR
            validated_data['onboarding_status'] = User.OnboardingStatus.PENDING_APPROVAL
            
            # super().create handles the password hashing and creation
            user = super().create(validated_data)

            # Create the profile with just the subtype; they fill the rest later
            VendorProfile.objects.create(
                user=user,
                subtype=vendor_subtype,
            )
            return user



class AttendeeRegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = AttendeeProfile
        fields = (
            "full_name",
            "email",
            "phone_number",
            # "reference_image",
        )

    def create(self, validated_data):
        return AttendeeProfile.objects.create(**validated_data)
        
                

# class RegisterSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)
#     password_confirm = serializers.CharField(write_only=True)

#     class Meta:
#         model = User
#         fields = (
#             "username",
#             "email",
#             "password",
#             "password_confirm",
#             "role",
#         )

#     def validate(self, attrs):
#         if attrs["password"] != attrs["password_confirm"]:
#             raise serializers.ValidationError({
#                 "password_confirm": "Passwords do not match."
#             })
#         validate_password(attrs["password"])
#         return attrs

#     def create(self, validated_data):
#         validated_data.pop("password_confirm")
#         role = validated_data.pop("role")
#         user = User.objects.create_user(
#             **validated_data,
#             role=role,
#             onboarding_status=User.OnboardingStatus.PENDING_EMAIL,
#             is_active=False,
#         )

#         return user

