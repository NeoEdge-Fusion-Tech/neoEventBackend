from rest_framework import serializers
from ..models import EventOwnerProfile, VendorProfile

class EventOwnerProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")
    email = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = EventOwnerProfile
        fields = (
            "username", "email", "organisation_name", "organisation_website", 
            "organisation_logo", "business_registration_number", 
            "is_business_verified", "total_events_created", "total_tickets_sold"
        )
        # These fields should only be updated by the system/admins
        read_only_fields = ("is_business_verified", "total_events_created", "total_tickets_sold")


class VendorProfileSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")
    email = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = VendorProfile
        fields = (
            "username", "email", "subtype", "bio", "profile_image", 
            "service_title", "service_areas", "years_of_experience", 
            "is_available_for_hire", "base_rate", "rate_unit", 
            "average_rating", "total_reviews"
        )
        # Prevent users from spoofing their own ratings
        read_only_fields = ("average_rating", "total_reviews")


# from rest_framework import serializers
# from ..models import EventOwnerProfile, VendorProfile, AttendeeProfile

# class EventOwnerProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EventOwnerProfile
#         exclude = ("id", "user", "created_at", "updated_at")

# class VendorProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = VendorProfile
#         exclude = ("id", "user", "created_at", "updated_at")

# class AttendeeProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AttendeeProfile
#         exclude = ("id", "user")

        