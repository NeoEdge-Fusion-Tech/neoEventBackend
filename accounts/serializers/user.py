from rest_framework import serializers
from ..models import User, EventOwnerProfile, VendorProfile
from .profiles import EventOwnerProfileSerializer, VendorProfileSerializer


class UserSerializer(serializers.ModelSerializer):
    owner_profile = EventOwnerProfileSerializer(read_only=True)
    vendor_profile = VendorProfileSerializer(read_only=True)
    vendor_business_id = serializers.SerializerMethodField()
    reference_image = serializers.SerializerMethodField()
    
    # is_verified = serializers.BooleanField(source="is_email_verified", read_only=True)
    available_profiles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "phone_number", "first_name", "last_name", 
            "role", "is_email_verified", "onboarding_status", "owner_profile", 
            "vendor_profile", "vendor_business_id", "date_joined", 
            "profile_image", "reference_image", "available_profiles"
        )
        read_only_fields = ("id", "role", "is_email_verified", "onboarding_status", "date_joined", "available_profiles")

    def get_available_profiles(self, obj):
        profiles = []
        if hasattr(obj, 'owner_profile') and obj.owner_profile:
            profiles.append(User.Role.OWNER)
        if hasattr(obj, 'vendor_profile') and obj.vendor_profile:
            profiles.append(User.Role.VENDOR)
        if hasattr(obj, 'attendee_profile') and obj.attendee_profile:
            profiles.append(User.Role.ATTENDEE)
        if hasattr(obj, 'validator_profile') and obj.validator_profile:
            profiles.append(User.Role.VALIDATOR)
        return profiles

    def get_vendor_business_id(self, obj):
        if hasattr(obj, 'vendor_business') and obj.vendor_business:
            return str(obj.vendor_business.id)
        return None

    def get_reference_image(self, obj):
        if hasattr(obj, 'attendee_profile') and obj.attendee_profile and obj.attendee_profile.reference_image:
            return obj.attendee_profile.reference_image.url
        return None


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
            
        from ..tasks import process_biometric_image
        image_url_to_process = None
        if hasattr(instance, 'attendee_profile') and instance.attendee_profile and instance.attendee_profile.reference_image:
            image_url_to_process = instance.attendee_profile.reference_image.url
        elif instance.profile_image:
            image_url_to_process = instance.profile_image.url
            
        if image_url_to_process:
            process_biometric_image.delay(instance.email, image_url_to_process, instance.id)
            
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

        from ..tasks import process_biometric_image
        image_url_to_process = None
        if hasattr(instance, 'attendee_profile') and instance.attendee_profile and instance.attendee_profile.reference_image:
            image_url_to_process = instance.attendee_profile.reference_image.url
        elif instance.profile_image:
            image_url_to_process = instance.profile_image.url
            
        if image_url_to_process:
            process_biometric_image.delay(instance.email, image_url_to_process, instance.id)

        return instance


class UpdateAttendeeProfileSerializer(serializers.ModelSerializer):
    """Allows attendees to update base profile fields."""
    profile_image = serializers.ImageField(required=False, allow_null=True)
    reference_image = serializers.ImageField(required=False, allow_null=True)

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

    def update(self, instance, validated_data):
        profile_image = validated_data.pop("profile_image", None)
        reference_image = validated_data.pop("reference_image", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if profile_image is not None:
            instance.profile_image = profile_image
            
        instance.save()

        if reference_image is not None:
            from ..models.attendee import AttendeeProfile
            profile, _ = AttendeeProfile.objects.get_or_create(user=instance)
            profile.reference_image = reference_image
            profile.save()
            
        from ..tasks import process_biometric_image
        image_url_to_process = None
        if hasattr(instance, 'attendee_profile') and instance.attendee_profile and instance.attendee_profile.reference_image:
            image_url_to_process = instance.attendee_profile.reference_image.url
        elif instance.profile_image:
            image_url_to_process = instance.profile_image.url
            
        if image_url_to_process:
            process_biometric_image.delay(instance.email, image_url_to_process, instance.id)
            
        return instance
        
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'attendee_profile') and instance.attendee_profile and instance.attendee_profile.reference_image:
            request = self.context.get('request')
            if request:
                ret['reference_image'] = request.build_absolute_uri(instance.attendee_profile.reference_image.url)
            else:
                ret['reference_image'] = instance.attendee_profile.reference_image.url
        else:
            ret['reference_image'] = None
        return ret

