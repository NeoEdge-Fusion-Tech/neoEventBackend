from rest_framework import serializers
from ..models import VendorRating

class VendorRatingSerializer(serializers.ModelSerializer):
    attendee_name = serializers.CharField(source='attendee.attendee_profile.full_name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.vendor_profile.business_name', read_only=True)

    class Meta:
        model = VendorRating
        fields = ['id', 'rating', 'review', 'created_at', 'attendee_name', 'vendor_name']
        read_only_fields = ['id', 'created_at']
