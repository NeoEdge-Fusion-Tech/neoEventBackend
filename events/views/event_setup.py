# events/views/event_setup.py
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import NotFound

from ..models import Event
from ..serializers import (
    EventListSerializer,
    EventDetailSerializer,
    EventCreateSerializer,
)
from ..permissions import IsEventOwnerRole


@extend_schema(
    tags=["Event Management"],
    summary="Create a new event",
    description="Allows authenticated users (Owners) to create a new event. The owner is automatically set to the current user."
)
class EventCreateView(generics.CreateAPIView):
    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated, IsEventOwnerRole]


@extend_schema(
    tags=["Events"],
    summary="List all public events",
    description="Retrieve a list of all events marked as public. Used for the public catalog (browse-to-register)."
)
class EventListView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]
    queryset = Event.objects.filter(is_public=True).select_related("owner")


@extend_schema(
    tags=["Event Management"],
    summary="List my events",
    description=(
        "Returns only the events owned by the authenticated user, including drafts "
        "and unpublished events — this is their private management dashboard. "
        "The super admin (role=ADMIN) sees every event on the platform."
    )
)
class OwnerEventListView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [IsAuthenticated, IsEventOwnerRole]

    def get_queryset(self):
        user = self.request.user
        queryset = Event.objects.select_related("owner")
        if user.role == user.Role.ADMIN:
            return queryset
        return queryset.filter(owner=user)


@extend_schema(
    tags=["Events"],
    summary="Get event details by slug",
    description=(
        "Retrieve detailed information about a specific event using its unique slug. "
        "Public events are visible to everyone (for registration). Non-public/draft "
        "events are only visible to their owner or the super admin."
    )
)
class EventDetailView(generics.RetrieveAPIView):
    serializer_class = EventDetailSerializer
    permission_classes = [AllowAny]
    queryset = Event.objects.select_related("owner")
    lookup_field = "slug"

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_value = self.kwargs[lookup_url_kwarg]

        import uuid
        try:
            uuid.UUID(str(filter_value))
            filter_kwargs = {'id': filter_value}
        except ValueError:
            filter_kwargs = {'slug': filter_value}

        obj = generics.get_object_or_404(queryset, **filter_kwargs)

        user = self.request.user
        is_owner_or_admin = bool(
            user
            and user.is_authenticated
            and (obj.owner_id == user.id or user.role == user.Role.ADMIN)
        )
        if not obj.is_public and not is_owner_or_admin:
            # 404 instead of 403 so we don't reveal that a private event exists
            raise NotFound("Event not found.")

        self.check_object_permissions(self.request, obj)
        return obj


@extend_schema(
    tags=["Event Management"],
    summary="Update an event",
    description="Allows the event owner to update event details using the Event ID (UUID)."
)
class EventUpdateView(generics.UpdateAPIView):
    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated, IsEventOwnerRole]
    queryset = Event.objects.all()
    lookup_field = "id"

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


@extend_schema(
    tags=["Event Management"],
    summary="Delete an event",
    description="Permanently remove an event. Restricted to the event owner."
)
class EventDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsEventOwnerRole]
    queryset = Event.objects.all()
    lookup_field = "id"


from rest_framework.views import APIView
from rest_framework.response import Response
from ..services.presigned import generate_event_setup_presigned_urls

@extend_schema(
    tags=["Event Management"],
    summary="Generate Pre-Signed S3 URLs for Event Setup Assets",
    description="Generates direct-to-S3 upload URLs (or local proxy URLs in dev) for event banners/flyers/videos before creating the event."
)
class EventPresignedUploadUrlView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        files = request.data.get("files", [])
        if not files or not isinstance(files, list):
            return Response({"error": "An array of 'files' is required"}, status=400)
            
        base_url = request.build_absolute_uri('/')[:-1]
        try:
            presigned_data = generate_event_setup_presigned_urls(files, base_url=base_url)
            return Response({"urls": presigned_data})
        except Exception as e:
            return Response({"error": str(e)}, status=500)


    

