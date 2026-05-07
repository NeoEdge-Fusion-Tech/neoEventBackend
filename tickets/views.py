from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny

from .models import TicketType, EventRegistration
from .serializers import TicketTypeSerializer, EventRegistrationSerializer

@extend_schema(
    tags=["Tickets"],
    summary="List available tickets for an event",
    description="Returns all active ticket types (Regular, VIP, etc.) for a specific event ID.",
    parameters=[
        OpenApiParameter(
            name="event_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="The UUID of the event",
        )
    ]
)
class EventTicketTypeListView(generics.ListAPIView):
    serializer_class = TicketTypeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return TicketType.objects.filter(
            event_id=self.kwargs["event_id"],
            is_active=True,
        )


@extend_schema(
    tags=["Registration"],
    summary="Register/Purchase a ticket",
    description=(
        "Registers an attendee for an event. If the attendee email doesn't exist, "
        "a new profile is created automatically. Updates ticket inventory on success."
    ),
    responses={
        201: EventRegistrationSerializer,
        400: OpenApiResponse(description="Validation error (e.g., Sold out or duplicate registration).")
    }
)
class EventRegistrationCreateView(generics.CreateAPIView):
    serializer_class = EventRegistrationSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Registration"],
    summary="Retrieve registration details",
    description="Get ticket and attendee details using the unique registration code (UUID) sent to the attendee.",
    responses={
        200: EventRegistrationSerializer,
        404: OpenApiResponse(description="Invalid or expired registration code.")
    }
)
class RegistrationDetailView(generics.RetrieveAPIView):
    serializer_class = EventRegistrationSerializer
    permission_classes = [AllowAny]
    queryset = EventRegistration.objects.select_related(
        "event",
        "attendee",
        "ticket_type",
    )
    lookup_field = "registration_code"

    