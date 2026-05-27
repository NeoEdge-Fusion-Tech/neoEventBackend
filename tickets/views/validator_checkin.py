from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
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

        attendee_name = registration.attendee.full_name if registration.attendee else registration.attendee_name
        attendee_email = registration.attendee.email if registration.attendee else registration.attendee_email
        ticket_type = registration.ticket_type.name if registration.ticket_type else "Regular"

        today = timezone.now().date()
        if DailyCheckIn.objects.filter(registration=registration, date=today).exists():
            return Response({
                "message": "Check-in successful",
                "attendee": {
                    "name": attendee_name,
                    "email": attendee_email,
                    "ticket_type": ticket_type,
                    "registration_code": registration.registration_code,
                    "checked_in": registration.checked_in,
                    "badge_print_count": registration.badge_print_count,
                    "last_badge_printed_at": registration.last_badge_printed_at.isoformat() if registration.last_badge_printed_at else None,
                    "profile_image": registration.attendee.reference_image.url if (registration.attendee and registration.attendee.reference_image) else None,
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
                "id": str(registration.id),
                "name": attendee_name,
                "email": attendee_email,
                "ticket_type": ticket_type,
                "registration_code": registration.registration_code,
                "checked_in": registration.checked_in,
                "badge_print_count": registration.badge_print_count,
                "last_badge_printed_at": registration.last_badge_printed_at.isoformat() if registration.last_badge_printed_at else None,
                "profile_image": registration.attendee.reference_image.url if (registration.attendee and registration.attendee.reference_image) else None
            }
        }, status=status.HTTP_200_OK)

class ValidatorAttendeeSearchView(APIView):
    """
    Search for attendees within a specific event by name, email, or ticket number.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not getattr(user, 'is_validator', False):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        event_id = request.query_params.get("event_id")
        query = request.query_params.get("q", "").strip()

        if not event_id:
            return Response({"detail": "event_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        qs = EventRegistration.objects.select_related("attendee", "ticket_type").filter(event_id=event_id)

        if query:
            qs = qs.filter(
                Q(registration_code__icontains=query) |
                Q(attendee_name__icontains=query) |
                Q(attendee_email__icontains=query) |
                Q(attendee__full_name__icontains=query) |
                Q(attendee__email__icontains=query)
            )

        # Limit to 50 results for performance
        qs = qs[:50]

        results = []
        for reg in qs:
            results.append({
                "registration_code": str(reg.registration_code),
                "name": reg.attendee.full_name if reg.attendee else reg.attendee_name,
                "email": reg.attendee.email if reg.attendee else reg.attendee_email,
                "ticket_type": reg.ticket_type.name if reg.ticket_type else "Regular",
                "status": reg.status,
                "checked_in": reg.checked_in,
                "badge_print_count": reg.badge_print_count,
                "last_badge_printed_at": reg.last_badge_printed_at.isoformat() if reg.last_badge_printed_at else None,
            })

        return Response(results, status=status.HTTP_200_OK)

class ValidatorMarkBadgePrintedView(APIView):
    """
    Marks a badge as printed, incrementing the count and updating the timestamp.
    Accepts: {"registration_code": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if not getattr(user, 'is_validator', False):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        code = request.data.get("registration_code")
        if not code:
            return Response(
                {"error": "registration_code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        registration = get_object_or_404(
            EventRegistration.objects.select_related("attendee", "ticket_type"),
            registration_code=code
        )

        registration.badge_print_count += 1
        registration.last_badge_printed_at = timezone.now()
        registration.save(update_fields=["badge_print_count", "last_badge_printed_at"])

        return Response({
            "message": "Badge print recorded successfully",
            "badge_print_count": registration.badge_print_count,
            "last_badge_printed_at": registration.last_badge_printed_at.isoformat()
        })
