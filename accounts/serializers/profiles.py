from rest_framework import serializers
from ..models import EventOwnerProfile, VendorProfile, AttendeeProfile

class EventOwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventOwnerProfile
        exclude = ("id", "user", "created_at", "updated_at")

class VendorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProfile
        exclude = ("id", "user", "created_at", "updated_at")

class AttendeeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendeeProfile
        exclude = ("id", "user")

        