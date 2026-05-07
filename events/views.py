from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Event
from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateSerializer,
)
from .permissions import IsEventOwner

@extend_schema(
    tags=["Events"],
    summary="List all public events",
    description="Retrieve a list of all events marked as public."
)
class EventListView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]
    queryset = Event.objects.filter(is_public=True).select_related("owner")


@extend_schema(
    tags=["Events"],
    summary="Get event details by slug",
    description="Retrieve detailed information about a specific event using its unique slug."
)
class EventDetailView(generics.RetrieveAPIView):
    serializer_class = EventDetailSerializer
    permission_classes = [AllowAny]
    queryset = Event.objects.select_related("owner")
    lookup_field = "slug"


@extend_schema(
    tags=["Event Management"],
    summary="Create a new event",
    description="Allows authenticated users (Owners) to create a new event. The owner is automatically set to the current user."
)
class EventCreateView(generics.CreateAPIView):
    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    tags=["Event Management"],
    summary="Update an event",
    description="Allows the event owner to update event details using the Event ID (UUID)."
)
class EventUpdateView(generics.UpdateAPIView):
    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated, IsEventOwner]
    queryset = Event.objects.all()
    lookup_field = "id"


@extend_schema(
    tags=["Event Management"],
    summary="Delete an event",
    description="Permanently remove an event. Restricted to the event owner."
)
class EventDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsEventOwner]
    queryset = Event.objects.all()
    lookup_field = "id"

    