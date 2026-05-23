# tickets/views/attendee_dashboard.py
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..models import EventRegistration
from ..serializers.attendee_dashboard import (
    AttendeeUpcomingEventSerializer,
    AttendeeEventHistorySerializer,
    AttendeeRegistrationDetailSerializer,
    AttendeeProfileSerializer,
    AttendeeActiveTicketSerializer,
)
from ..models import (
    EventRegistration,
    TicketType,
)
from accounts.models import AttendeeProfile


@extend_schema(tags=["Attendee Dashboard"])
class MyUpcomingEventsView(generics.ListAPIView):
    serializer_class = AttendeeUpcomingEventSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get My Upcoming Events",
        description="Returns all upcoming events the authenticated attendee has registered for.",
        responses={200: AttendeeUpcomingEventSerializer(many=True)},
    )
    def get_queryset(self):
        attendee_profile = getattr(self.request.user, "attendee_profile", None)
        if not attendee_profile:
            return EventRegistration.objects.none()

        now = timezone.now()

        return (
            EventRegistration.objects
            .select_related("event", "ticket_type", "attendee")
            .filter(
                attendee=attendee_profile,
                event__end_date__gte=now,
            )
            .exclude(status=EventRegistration.Status.CANCELLED)
            .order_by("event__start_date")
        )


@extend_schema(tags=["Attendee Dashboard"])
class MyPastEventsView(generics.ListAPIView):
    serializer_class = AttendeeEventHistorySerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get My Past Events",
        description="Returns all past events the authenticated attendee has registered for.",
        responses={200: AttendeeEventHistorySerializer(many=True)},
    )
    def get_queryset(self):
        attendee_profile = getattr(self.request.user, "attendee_profile", None)
        if not attendee_profile:
            return EventRegistration.objects.none()

        now = timezone.now()

        return (
            EventRegistration.objects
            .select_related("event", "ticket_type", "attendee")
            .filter(
                attendee=attendee_profile,
                event__end_date__lt=now,
            )
            .exclude(status=EventRegistration.Status.CANCELLED)
            .order_by("-event__start_date")
        )


@extend_schema(tags=["Attendee Dashboard"])
class MyRegistrationDetailView(generics.RetrieveAPIView):
    serializer_class = AttendeeRegistrationDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "registration_code"

    @extend_schema(
        summary="Get Registration Detail",
        description="Retrieve detailed information about a specific registration using registration_code.",
        responses={200: AttendeeRegistrationDetailSerializer},
    )
    def get_queryset(self):
        attendee_profile = getattr(self.request.user, "attendee_profile", None)
        if not attendee_profile:
            return EventRegistration.objects.none()

        return EventRegistration.objects.select_related(
            "event", "ticket_type", "attendee"
        ).filter(attendee=attendee_profile)


@extend_schema(tags=["Attendee Dashboard"])
class CancelRegistrationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Cancel Event Registration",
        description="Cancel a registration. Only allowed before check-in and if not already cancelled.",
        request=None,
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "registration_id": {"type": "string"},
                        "event_title": {"type": "string"},
                    }
                },
                description="Registration cancelled successfully"
            ),
            400: OpenApiResponse(description="Bad Request (already cancelled or checked-in)"),
            404: OpenApiResponse(description="Registration not found or no attendee profile"),
        },
    )
    @transaction.atomic
    def post(self, request, id):
        attendee_profile = getattr(request.user, "attendee_profile", None)

        if not attendee_profile:
            return Response(
                {"detail": "No attendee profile linked to this account."},
                status=status.HTTP_404_NOT_FOUND,
            )

        registration = get_object_or_404(
            EventRegistration.objects.select_related("ticket_type", "event"),
            id=id,
            attendee=attendee_profile,
        )

        if registration.status == EventRegistration.Status.CANCELLED:
            return Response(
                {"detail": "This registration has already been cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if registration.checked_in:
            return Response(
                {"detail": "Checked-in registrations cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Restore ticket inventory
        if registration.ticket_type and registration.ticket_type.sold_count > 0:
            registration.ticket_type.sold_count -= 1
            registration.ticket_type.save(update_fields=["sold_count"])

        # Cancel registration
        registration.status = EventRegistration.Status.CANCELLED
        registration.save(update_fields=["status"])

        return Response(
            {
                "message": "Registration cancelled successfully.",
                "registration_id": str(registration.id),
                "event_title": registration.event.title,
            },
            status=status.HTTP_200_OK,
        )
    

# # For Gate Entry 
class MyActiveTicketsView(generics.ListAPIView):
    serializer_class = AttendeeActiveTicketSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="My Active Tickets",
        description="Returns active upcoming tickets optimized for gate scanning and QR validation.",
        responses={200: AttendeeActiveTicketSerializer(many=True)},
    )
    def get_queryset(self):
        attendee_profile = getattr(self.request.user, "attendee_profile", None)
        if not attendee_profile:
            return EventRegistration.objects.none()

        now = timezone.now()

        return EventRegistration.objects.select_related(
            "event", "ticket_type", "attendee"
        ).filter(
            attendee=attendee_profile,
            event__end_date__gte=now,
            status=EventRegistration.Status.CONFIRMED,
        ).exclude(
            status=EventRegistration.Status.CANCELLED
        ).order_by("event__start_date")

@extend_schema(tags=["Attendee Profile"])
class MyAttendeeProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /me/attendee-profile/  → Get attendee profile
    PATCH /me/attendee-profile/ → Update profile (completion)
    """
    serializer_class = AttendeeProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Returns the attendee profile linked to the logged-in user
        attendee_profile = getattr(self.request.user, "attendee_profile", None)
        if not attendee_profile:
            # You can raise 404 or create on-the-fly depending on your logic
            raise Http404("Attendee profile not found.")
        return attendee_profile

    @extend_schema(
        summary="Get My Attendee Profile",
        description="Retrieve attendee profile details for the currently authenticated user.",
        responses={200: AttendeeProfileSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update My Attendee Profile",
        description="Update attendee profile (useful for profile completion, photo upload, consent, etc.)",
        responses={200: AttendeeProfileSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


@extend_schema(tags=["Attendee Dashboard"])
class PaymentHistoryView(generics.ListAPIView):
    """
    Returns a payment history derived from the attendee's ticket purchases.
    Each registration with a ticket_price > 0 appears as a payment record.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Payment History",
        description="Returns all ticket purchase records for the authenticated attendee, ordered newest first.",
    )
    def get_queryset(self):
        attendee_profile = getattr(self.request.user, "attendee_profile", None)
        if not attendee_profile:
            return EventRegistration.objects.none()
        return (
            EventRegistration.objects
            .select_related("event", "ticket_type")
            .filter(attendee=attendee_profile)
            .exclude(status=EventRegistration.Status.CANCELLED)
            .order_by("-registered_at")
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = []
        for reg in qs:
            data.append({
                "id": str(reg.id),
                "registration_code": reg.registration_code,
                "event_title": reg.event.title if reg.event else "",
                "event_start_date": reg.event.start_date if reg.event else None,
                "ticket_type": reg.ticket_type.name if reg.ticket_type else "General Admission",
                "amount": str(reg.ticket_type.price) if reg.ticket_type else "0.00",
                "currency": reg.event.currency if reg.event else "USD",
                "status": reg.status,
                "paid_at": reg.registered_at,
                "is_free": float(reg.ticket_type.price) == 0 if reg.ticket_type else True,
            })
        return Response(data)