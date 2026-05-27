from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from ..models import EventOwnerProfile, VendorProfile
from ..serializers import EventOwnerProfileSerializer, VendorProfileSerializer


@extend_schema(tags=["Profiles"], 
               summary="Update Owner Profile"
               )
class EventOwnerProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = EventOwnerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Automatically fetch the profile for the logged-in owner
        return self.request.user.owner_profile


@extend_schema(tags=["Profiles"], summary="Update Vendor Profile")
class VendorProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Automatically fetch the profile for the logged-in vendor
        return self.request.user.vendor_profile

@extend_schema(tags=["Profiles"], summary="Update Attendee/User Base Profile")
class AttendeeProfileUpdateView(generics.RetrieveUpdateAPIView):
    from ..serializers.user import UpdateAttendeeProfileSerializer
    serializer_class = UpdateAttendeeProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
