from rest_framework import generics

from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from events.models import Event
from events.permissions import IsEventOwnerRole

from ..models import Photo
from ..serializers import PhotoSerializer
from ..permissions import CanUploadPhotos


@extend_schema(
    tags=["Photos"],
    summary="Upload event photo",
    description=(
        "Allows confirmed photographers assigned "
        "to an event to upload photos."
    ),
)
class PhotoUploadView(generics.CreateAPIView):

    serializer_class = PhotoSerializer

    permission_classes = [
        IsAuthenticated,
        CanUploadPhotos,
    ]

    def perform_create(self, serializer):

        event = Event.objects.get(
            id=self.kwargs["event_id"]
        )

        serializer.save(
            event=event,
            uploader=self.request.user,
        )


@extend_schema(
    tags=["Photos"],
    summary="List event photos",
)
class PhotoListView(generics.ListAPIView):

    serializer_class = PhotoSerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Photo.objects.filter(
            event_id=self.kwargs["event_id"]
        ).select_related(
            "uploader",
            "event",
        )


@extend_schema(
    tags=["Photos"],
    summary="Attendee Gallery View",
    description="Returns personal or public photos for an event."
)
class EventGalleryView(generics.ListAPIView):
    serializer_class = PhotoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        event_id = self.request.query_params.get("event_id")
        category = self.request.query_params.get("category", "public")
        
        if not event_id:
            return Photo.objects.none()

        if category == "personal":
            return Photo.objects.filter(event_id=event_id, mapped_users__user=self.request.user)
        else:
            return Photo.objects.filter(event_id=event_id)
import io
import zipfile
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from ..tasks import notify_users_of_mapped_gallery

@extend_schema(
    tags=["Photos"],
    summary="Download personal gallery as ZIP",
    description="Dynamically generates a ZIP file of all photos mapped to the authenticated user for the event."
)
class PersonalGalleryZipView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        # 1. Get all photos mapped to the user
        mapped_photos = Photo.objects.filter(event_id=event_id, mapped_users__user=request.user)
        
        if not mapped_photos.exists():
            return Response({"detail": "No personal photos found."}, status=404)
            
        # 2. Create in-memory zip
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for photo in mapped_photos:
                # Add each file to the zip
                # The filename inside the zip will just be the basename of the media file
                file_name = photo.media_file.name.split('/')[-1]
                
                # Note: If storing locally, we can read directly. For S3, .read() downloads it.
                try:
                    with photo.media_file.open('rb') as f:
                        zip_file.writestr(file_name, f.read())
                except Exception as e:
                    print(f"Failed to zip {file_name}: {e}")
                    
        # 3. Return as response
        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="neoevents_gallery_{event_id}.zip"'
        return response


@extend_schema(
    tags=["Photos"],
    summary="Notify attendees of their galleries",
    description="Triggers a background task to email all attendees who have mapped photos."
)
class NotifyAttendeesView(APIView):
    permission_classes = [IsAuthenticated, IsEventOwnerRole]
    
    def post(self, request, event_id):
        # Optional: verify event exists
        notify_users_of_mapped_gallery.delay(event_id)
        return Response({"status": "Emails are being sent in the background."})

