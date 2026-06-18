from rest_framework import generics

from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from events.models import Event
from events.permissions import IsEventOwnerRole

from ..models import Photo
from ..serializers import PhotoSerializer
from ..permissions import CanUploadPhotos

import logging
logger = logging.getLogger(__name__)
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from rest_framework.parsers import BaseParser
# Conditional import of cloudinary
try:
    import cloudinary
    import cloudinary.uploader
except ImportError:
    cloudinary = None
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from rest_framework.parsers import BaseParser


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
from django.db.models import Count
from ..tasks import notify_users_of_mapped_gallery


@extend_schema(
    tags=["Photos"],
    summary="Event Owner Gallery",
    description=(
        "Returns all photos for an event visible to the event owner. "
        "Optional ?photographer=<user_id> filter. "
        "Also returns a photographers list for dropdown population."
    )
)
class EventOwnerGalleryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        from django.shortcuts import get_object_or_404
        from events.models import Event

        event = get_object_or_404(Event, id=event_id)

        if event.owner != request.user:
            return Response({"detail": "Only the event owner can access this gallery."}, status=403)

        qs = Photo.objects.filter(event=event).select_related("uploader")

        photographer_id = request.query_params.get("photographer")
        if photographer_id:
            qs = qs.filter(uploader_id=photographer_id)

        # Build list of distinct photographers for this event
        photographer_qs = (
            Photo.objects.filter(event=event)
            .values(
                "uploader__id",
                "uploader__username",
                "uploader__first_name",
                "uploader__last_name",
                "uploader__email",
            )
            .annotate(photo_count=Count("id"))
            .order_by("uploader__username")
        )
        photographers = [
            {
                "id": str(p["uploader__id"]),
                "username": p["uploader__username"],
                "full_name": (
                    f"{p['uploader__first_name']} {p['uploader__last_name']}".strip()
                    or p["uploader__username"]
                ),
                "email": p["uploader__email"],
                "photo_count": p["photo_count"],
            }
            for p in photographer_qs
        ]

        serializer = PhotoSerializer(qs, many=True, context={"request": request})

        return Response({
            "photographers": photographers,
            "photos": serializer.data,
            "total": qs.count(),
        })


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
        from core.sqs import dispatch_task
        dispatch_task("notify_users_of_mapped_gallery", {"event_id": event_id})
        return Response({"status": "Emails are being sent in the background."})

from ..services.s3 import generate_bulk_presigned_upload_urls
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

@extend_schema(
    tags=["Photos"],
    summary="Generate Bulk Pre-Signed S3 URLs",
    description="Generates an array of direct-to-S3 upload URLs for a vendor."
)
class GeneratePresignedUrlView(APIView):
    permission_classes = [IsAuthenticated, CanUploadPhotos]
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        files = request.data.get("files", [])
        if not files or not isinstance(files, list):
            return Response({"error": "An array of 'files' is required"}, status=400)
            
        try:
            presigned_data = generate_bulk_presigned_upload_urls(
                event_name=event.name,
                event_id=str(event.id),
                files=files
            )
            return Response({"urls": presigned_data})
        except Exception as e:
            return Response({"error": str(e)}, status=500)


@extend_schema(
    tags=["Photos"],
    summary="Confirm Bulk S3 Uploads",
    description="Called by the frontend after a bulk S3 upload finishes. Bulk-creates Photo records and triggers AI."
)
class ConfirmBulkS3UploadView(APIView):
    permission_classes = [IsAuthenticated, CanUploadPhotos]
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        
        # Array of full S3 URLs that successfully uploaded
        full_urls = request.data.get("full_urls", [])
        
        if not full_urls or not isinstance(full_urls, list):
            return Response({"error": "'full_urls' array is required"}, status=400)
            
        # Bulk Create Photos
        photos_to_create = [
            Photo(
                event=event,
                uploader=request.user,
                # We save the full S3 URL directly to the media_file field.
                # Assuming media_file is a FileField, passing the URL as a string can work,
                # or you may need to adjust the model to use URLField if not using django-storages.
                media_file=url

            )
            for url in full_urls
        ]
        
        created_photos = Photo.objects.bulk_create(photos_to_create)
        
        # Trigger Celery/SQS Task with the new photo IDs
        photo_ids = [p.id for p in created_photos]
        from core.sqs import dispatch_task
        dispatch_task("extract_faces_from_photos", {"photo_ids": photo_ids})
        
        return Response({
            "status": "success",
            "message": f"{len(photo_ids)} photos confirmed and queued for AI mapping."
        })

    from django.conf import settings
    import logging
    logger = logging.getLogger(__name__)
    
    # Conditionally import cloudinary if available
    try:
        import cloudinary.uploader
    except ImportError:
        cloudinary = None

class RawBytesParser(BaseParser):
    """
    Parser to accept raw bytes directly from a PUT request.
    """
    media_type = '*/*'
    
    def parse(self, stream, media_type=None, parser_context=None):
        return stream.read()

from rest_framework.parsers import MultiPartParser, FormParser

@extend_schema(
    tags=["Photos"],
    summary="Local Direct Upload (Dev Only)",
    description="Intercepts PUT requests in local development to simulate S3 direct uploads."
)
class CloudinaryUploadView(APIView):
    def get_permissions(self):
        if self.request.method == 'PUT':
            return []
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]

    def get_parsers(self):
        if self.request.method == 'PUT':
            return [RawBytesParser()]
        return [MultiPartParser(), FormParser()]

    def post(self, request, *args, **kwargs):
        # Expect a file under 'file' key
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({"error": "No file provided."}, status=400)
        if not getattr(settings, "USE_CLOUDINARY", False) or not cloudinary:
            return Response({"error": "Cloudinary not configured."}, status=500)
        try:
            # Convert InMemoryUploadedFile to bytes for cloudinary
            file_data = uploaded_file.read()
            from io import BytesIO
            file_obj = BytesIO(file_data)
            upload_result = cloudinary.uploader.upload(
                file_obj,
                folder="uploads",
                public_id=uploaded_file.name,
                resource_type="auto",
            )
            url = upload_result.get('secure_url') or upload_result.get('url')
            return Response({"status": "success", "url": url, "public_id": upload_result.get('public_id')})
        except Exception as e:
            logger.exception("Cloudinary upload failed")
            return Response({"error": str(e)}, status=500)
    # The frontend uploads directly without Django auth tokens via PUT,
    # so we allow any, since it's just simulating the public S3 URL in dev.

    def put(self, request, filepath):
        # Disable in production (when USE_S3 is True)
        # In production (USE_S3) we do not accept raw PUT uploads; clients should use presigned URLs.
        if getattr(settings, "USE_S3", False):
            return Response({"error": "Direct upload disabled in production. Use presigned URL endpoint."}, status=403)

        try:
            raw_data = request.data
            # Ensure Cloudinary is configured; backend must upload to Cloudinary.
            if not getattr(settings, "USE_CLOUDINARY", False) or not cloudinary:
                return Response({"error": "Cloudinary not configured for backend upload."}, status=500)
            from io import BytesIO
            file_obj = BytesIO(raw_data)
            upload_result = cloudinary.uploader.upload(
                file_obj,
                public_id=filepath,
                resource_type="auto",
            )
            url = upload_result.get("secure_url") or upload_result.get("url")
            return Response({
                "status": "success",
                "url": url,
                "public_id": upload_result.get("public_id"),
            })
        except Exception as e:
            logger.exception("Cloudinary upload failed in backend")
            return Response({"error": str(e)}, status=500)
