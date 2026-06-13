from rest_framework import serializers
from ..models import EventOwnerProfile, VendorProfile

class EventOwnerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", required=False)
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    phone_number = serializers.CharField(source="user.phone_number", required=False, allow_blank=True)
    email = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = EventOwnerProfile
        fields = (
            "username", "first_name", "last_name", "phone_number", "email", "organisation_name", "organisation_website", 
            "organisation_logo", "business_registration_number", 
            "is_business_verified", "total_events_created", "total_tickets_sold"
        )
        # These fields should only be updated by the system/admins
        read_only_fields = ("is_business_verified", "total_events_created", "total_tickets_sold")

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            if 'username' in user_data:
                instance.user.username = user_data['username']
            if 'first_name' in user_data:
                instance.user.first_name = user_data['first_name']
            if 'last_name' in user_data:
                instance.user.last_name = user_data['last_name']
            if 'phone_number' in user_data:
                instance.user.phone_number = user_data['phone_number']
            instance.user.save()
        return super().update(instance, validated_data)


class VendorProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", required=False)
    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)
    phone_number = serializers.CharField(source="user.phone_number", required=False, allow_blank=True)
    email = serializers.ReadOnlyField(source="user.email")

    class Meta:
        model = VendorProfile
        fields = (
            "username", "first_name", "last_name", "phone_number", "email", "subtype", "bio", "profile_image", 
            "service_title", "service_areas", "years_of_experience", 
            "is_available_for_hire", "base_rate", "rate_unit", 
            "average_rating", "total_reviews"
        )
        # Prevent users from spoofing their own ratings
        read_only_fields = ("average_rating", "total_reviews")

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            if 'username' in user_data:
                instance.user.username = user_data['username']
            if 'first_name' in user_data:
                instance.user.first_name = user_data['first_name']
            if 'last_name' in user_data:
                instance.user.last_name = user_data['last_name']
            if 'phone_number' in user_data:
                instance.user.phone_number = user_data['phone_number']
            instance.user.save()
        return super().update(instance, validated_data)


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

        