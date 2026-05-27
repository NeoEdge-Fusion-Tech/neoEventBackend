from rest_framework import serializers
from ..models import User, EventOwnerProfile, VendorProfile
from .profiles import EventOwnerProfileSerializer, VendorProfileSerializer


class UserSerializer(serializers.ModelSerializer):
    owner_profile = EventOwnerProfileSerializer(read_only=True)
    vendor_profile = VendorProfileSerializer(read_only=True)
    
    # is_verified = serializers.BooleanField(source="is_email_verified", read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "last_name", 
            "role", "is_email_verified", "onboarding_status", "owner_profile", 
            "vendor_profile", "date_joined",
        )
        read_only_fields = ("id", "role", "is_email_verified", "onboarding_status", "date_joined")


class UpdateOwnerProfileSerializer(serializers.ModelSerializer):
    owner_profile = EventOwnerProfileSerializer()

    class Meta:
        model = User
        fields = ("first_name", "last_name", "owner_profile")

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("owner_profile", {})
        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Update Profile fields
        if profile_data:
            profile, _ = EventOwnerProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        return instance



class UpdateVendorProfileSerializer(serializers.ModelSerializer):
    """Allows vendors to update their service profile."""

    vendor_profile = VendorProfileSerializer()

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone_number",
            "profile_image",
            "bio",
            "portfolio_website",
            "instagram_handle",
            "twitter_handle",
            "vendor_profile",
        )

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("vendor_profile", {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data:
            profile, _ = VendorProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class UpdateAttendeeProfileSerializer(serializers.ModelSerializer):
    """Allows attendees to update base profile fields."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "role",
            "first_name",
            "last_name",
            "phone_number",
            "profile_image",
            "reference_image",
        )
        read_only_fields = ("id", "username", "email", "role")
        
