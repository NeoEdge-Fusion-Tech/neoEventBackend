from rest_framework import generics

from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from events.models import Event

from ..models import EventPhoto

from ..serializers import EventPhotoSerializer

from ..permissions import CanUploadEventPhotos


@extend_schema(
    tags=["Photos"],
    summary="Upload event photo",
    description=(
        "Allows confirmed photographers assigned "
        "to an event to upload photos."
    ),
)
class EventPhotoUploadView(generics.CreateAPIView):

    serializer_class = EventPhotoSerializer

    permission_classes = [
        IsAuthenticated,
        CanUploadEventPhotos,
    ]

    def perform_create(self, serializer):

        event = Event.objects.get(
            id=self.kwargs["event_id"]
        )

        serializer.save(
            event=event,
            uploaded_by=self.request.user,
        )


@extend_schema(
    tags=["Photos"],
    summary="List event photos",
)
class EventPhotoListView(generics.ListAPIView):

    serializer_class = EventPhotoSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return EventPhoto.objects.filter(
            event_id=self.kwargs["event_id"]
        ).select_related(
            "uploaded_by",
            "event",
        )