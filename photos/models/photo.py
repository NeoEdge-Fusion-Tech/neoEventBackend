import uuid
from django.db import models
from django.conf import settings
from core.models import UUIDPkField
from pgvector.django import VectorField

def event_gallery_upload_path(instance, filename):
    event_str = str(instance.event.id)[:6]
    event_name = instance.event.title.replace(' ', '_').lower()
    return f"events/gallery/{event_name}_{event_str}/{filename}"

class Photo(UUIDPkField):
    class AIProcessingStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending AI Detection'
        FACES_DETECTED = 'FACES_DETECTED', 'Faces Detected'
        MAPPED_TO_USERS = 'MAPPED_TO_USERS', 'Mapped to Users'
        FAILED = 'FAILED', 'Processing Failed'

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="photos",
    )

    uploader = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="uploaded_event_photos",
    )

    media_file = models.ImageField(upload_to=event_gallery_upload_path)
    thumbnail_url = models.URLField(blank=True, null=True)

    caption = models.CharField(max_length=255, blank=True)
    is_public = models.BooleanField(default=True)
    
    ai_status = models.CharField(
        max_length=20, 
        choices=AIProcessingStatus.choices, 
        default=AIProcessingStatus.PENDING
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["uploader"]),
            models.Index(fields=["ai_status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.event.title} - {self.uploader.username}"
    

class PhotoFace(UUIDPkField):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name="faces")
    # InsightFace 512D embedding
    face_embedding = VectorField(dimensions=512)
    # [x1, y1, x2, y2]
    bounding_box = models.JSONField(null=True, blank=True)
    confidence = models.FloatField(default=0.0)

    class Meta:
        indexes = [
            models.Index(fields=["photo"])
        ]


class UserPhoto(UUIDPkField):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="my_event_gallery"
    )
    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name="mapped_users"
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="attendee_galleries"
    )
    confidence_score = models.FloatField(default=0.0)
    source = models.CharField(max_length=50, default='AI')

    class Meta:
        unique_together = ("user", "photo")
        indexes = [
            models.Index(fields=['user', 'event']),
        ]