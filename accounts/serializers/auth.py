# serializers/auth.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from ..models import User, VendorProfile, EventOwnerProfile, AttendeeProfile
from .user import UserSerializer
from django.db import transaction
from ..utils.otp import generate_and_send_otp

class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    user = UserSerializer()


class VerifyEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class ResendEmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    default_error_messages = {
        "no_active_account": "Invalid credentials."
    }

    def validate(self, attrs):
        # Allow email to be passed in the 'username' field
        username = attrs.get('username')
        if username and '@' in username:
            try:
                user = User.objects.get(email=username)
                attrs['username'] = user.username
            except User.DoesNotExist:
                pass
                
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data

class BaseRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = User
        fields = ("username", "email", "password", "password_confirm", "first_name", "last_name")

    def validate(self, attrs):
        if not attrs.get("username"):
            attrs["username"] = attrs.get("email")
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
        fields = ("username", "email", "first_name", "last_name", "phone_number", "password", "password_confirm")

    def create(self, validated_data):
        with transaction.atomic():
            # Set the role internally so it's not a dropdown in Swagger
            validated_data['role'] = User.Role.OWNER
            
            # This calls BaseRegisterSerializer.create()
            user = super().create(validated_data)
            
            # Create the one-to-one profile
            EventOwnerProfile.objects.create(user=user)
            
            # Generate and send OTP for email verification
            generate_and_send_otp(user)
            
            return user
        

from vendors.models import VendorBusiness

from events.models.vendor import EventVendor

class VendorRegisterSerializer(BaseRegisterSerializer):
    vendor_subtype = serializers.CharField(max_length=50)
    business_name = serializers.CharField(max_length=255)
    is_registered = serializers.BooleanField(default=False)
    registration_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country_of_registration = serializers.CharField(max_length=100, required=False, allow_blank=True)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state_or_county = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)

    class Meta(BaseRegisterSerializer.Meta):
        fields = (
            "username", "email", "first_name", "last_name", "phone_number", "password", "password_confirm", 
            "vendor_subtype", "business_name", "is_registered", "registration_number",
            "country_of_registration", "address", "city", "state_or_county", "country"
        )

    def create(self, validated_data):
        vendor_subtype = validated_data.pop("vendor_subtype")
        business_name = validated_data.pop("business_name")
        is_registered = validated_data.pop("is_registered", False)
        registration_number = validated_data.pop("registration_number", "")
        country_of_registration = validated_data.pop("country_of_registration", "")
        address = validated_data.pop("address")
        city = validated_data.pop("city", "")
        state_or_county = validated_data.pop("state_or_county", "")
        country = validated_data.pop("country", "")

        with transaction.atomic():
            validated_data['role'] = User.Role.VENDOR
            # We set them to pending email first; after verification they can move to PENDING_APPROVAL
            validated_data['onboarding_status'] = User.OnboardingStatus.PENDING_EMAIL
            
            user = super().create(validated_data)

            VendorProfile.objects.create(
                user=user,
                subtype=vendor_subtype.upper(),
            )
            
            VendorBusiness.objects.create(
                user=user,
                business_name=business_name,
                is_registered=is_registered,
                registration_number=registration_number,
                country_of_registration=country_of_registration,
                address=address,
                city=city,
                state_or_county=state_or_county,
                country=country,
                email=user.email,
                phone_number=user.phone_number
            )
            
            # Link any pending event invitations for this email to the newly created user
            EventVendor.objects.filter(invited_email=user.email, vendor__isnull=True).update(vendor=user)
            
            # Generate and send OTP for email verification
            generate_and_send_otp(user)
            
            return user



class AttendeeRegistrationSerializer(serializers.ModelSerializer):
    reference_image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = AttendeeProfile
        fields = (
            "full_name", "email", "phone_number", "reference_image",
        )

    def create(self, validated_data):
        profile = AttendeeProfile.objects.create(**validated_data)
        if profile.reference_image:
            from ..tasks import process_biometric_image
            # No user ID yet, so we just pass the email and image
            process_biometric_image.delay(profile.email, profile.reference_image.url, None)
        return profile
        
                 
class AttendeeRegisterSerializer(BaseRegisterSerializer):
    phone_number = serializers.CharField(required=False, allow_blank=True)

    class Meta(BaseRegisterSerializer.Meta):
        fields = (
            "username", "email", "phone_number", "password", "password_confirm", 
            "first_name", "last_name"
        )

    def create(self, validated_data):
        phone_number = validated_data.pop("phone_number", "")
        with transaction.atomic():
            validated_data['role'] = User.Role.ATTENDEE
            validated_data['onboarding_status'] = User.OnboardingStatus.PENDING_EMAIL
            
            # This calls BaseRegisterSerializer.create()
            user = super().create(validated_data)
            
            # Check if an AttendeeProfile already exists for this email (e.g. from event registration)
            attendee = AttendeeProfile.objects.filter(email=user.email).first()
            if attendee:
                attendee.user = user
                if not attendee.phone_number:
                    attendee.phone_number = phone_number
                attendee.save()
            else:
                attendee = AttendeeProfile.objects.create(
                    user=user,
                    email=user.email,
                    full_name=f"{user.first_name} {user.last_name}".strip() or user.username,
                    phone_number=phone_number,
                )
                
            # Send the welcome email since they EXPRESSLY signed up for a platform account!
            from ..services.emails import send_welcome_email
            send_welcome_email(attendee)
            
            # Generate and send OTP for email verification
            generate_and_send_otp(user)
            
            return user
        
                

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

