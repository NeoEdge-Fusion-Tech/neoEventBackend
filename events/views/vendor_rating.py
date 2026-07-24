from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ..models import VendorRating, Event, EventVendor
from ..serializers.vendor_rating import VendorRatingSerializer

class RateVendorView(generics.CreateAPIView):
    serializer_class = VendorRatingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        event_id = self.kwargs.get('event_id')
        vendor_id = self.kwargs.get('vendor_id')

        event = get_object_or_404(Event, id=event_id)
        
        # Check if the vendor is actually assigned to this event
        if not EventVendor.objects.filter(event=event, vendor_id=vendor_id).exists():
            raise ValidationError("This vendor is not associated with this event.")

        # Check if the user has already rated
        if VendorRating.objects.filter(vendor_id=vendor_id, event=event, attendee=self.request.user).exists():
            raise ValidationError("You have already rated this vendor for this event.")

        serializer.save(
            attendee=self.request.user,
            event=event,
            vendor_id=vendor_id
        )

class VendorEventRatingsListView(generics.ListAPIView):
    serializer_class = VendorRatingSerializer

    def get_queryset(self):
        event_id = self.kwargs.get('event_id')
        vendor_id = self.kwargs.get('vendor_id')
        return VendorRating.objects.filter(event_id=event_id, vendor_id=vendor_id).order_by('-created_at')
