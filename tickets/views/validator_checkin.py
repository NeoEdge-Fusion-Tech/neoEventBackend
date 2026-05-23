from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import EventRegistration, DailyCheckIn

class ValidatorCheckInView(APIView):
    """
    Check-in API for the mobile validation app.
    Takes event_id, ticket_id (registration_code), timestamp, and device_validator_id.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not getattr(user, 'is_validator', False):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        event_id = request.data.get("event_id")
        registration_code = request.data.get("ticket_id")
        device_id = request.data.get("device_validator_id", user.validator_profile.device_name if hasattr(user, 'validator_profile') else "validator")

        registration = get_object_or_404(
            EventRegistration.objects.select_related("attendee", "ticket_type"),
            registration_code=registration_code,
            event_id=event_id
        )

        today = timezone.now().date()
        if DailyCheckIn.objects.filter(registration=registration, date=today).exists():
            # Return attendee details even if already verified
            return Response({
                "detail": "Already Verified",
                "attendee": {
                    "name": f"{registration.attendee.first_name} {registration.attendee.last_name}".strip() if registration.attendee else registration.guest_full_name,
                    "email": registration.attendee.email if registration.attendee else registration.guest_email,
                    "ticket_type": registration.ticket_type.name if registration.ticket_type else "Regular",
                    "profile_image": registration.attendee.profile_image.url if (registration.attendee and registration.attendee.profile_image) else None
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check them in
        DailyCheckIn.objects.create(
            registration=registration,
            device_id=device_id
        )

        if not registration.checked_in:
            registration.checked_in = True
            registration.status = EventRegistration.Status.CHECKED_IN
            registration.save(update_fields=["checked_in", "status"])

        return Response({
            "message": "Validated successfully.",
            "attendee": {
                "name": f"{registration.attendee.first_name} {registration.attendee.last_name}".strip() if registration.attendee else registration.guest_full_name,
                "email": registration.attendee.email if registration.attendee else registration.guest_email,
                "ticket_type": registration.ticket_type.name if registration.ticket_type else "Regular",
                "profile_image": registration.attendee.profile_image.url if (registration.attendee and registration.attendee.profile_image) else None
            }
        }, status=status.HTTP_200_OK)
