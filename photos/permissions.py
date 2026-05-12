from rest_framework.permissions import BasePermission

from events.models import EventVendor


class CanUploadEventPhotos(BasePermission):

    message = (
        "Only confirmed photographers assigned "
        "to this event can upload photos."
    )

    def has_permission(self, request, view):

        event_id = view.kwargs.get("event_id")

        if not request.user.is_authenticated:
            return False

        return EventVendor.objects.filter(
            event_id=event_id,
            vendor=request.user,
            role=EventVendor.VendorRole.PHOTOGRAPHER,
            is_confirmed=True,
        ).exists()

        