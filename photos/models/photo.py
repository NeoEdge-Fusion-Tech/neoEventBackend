from django.db import models
from core.models import UUIDPkField


class EventPhoto(UUIDPkField):
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="photos",
    )

    uploaded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="uploaded_event_photos",
    )

    image = models.ImageField(
        upload_to="event_photos/"
    )

    caption = models.CharField(
        max_length=255,
        blank=True,
    )

    is_processed = models.BooleanField(default=False)

    detected_users = models.ManyToManyField(
        "accounts.User",
        related_name="detected_in_photos",
        blank=True
    )


    class Meta:

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["uploaded_by"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):

        return f"{self.event.title} - {self.uploaded_by.username}"
    

class FaceEmbedding(UUIDPkField):
    photo = models.ForeignKey(EventPhoto, on_delete=models.CASCADE, related_name="embeddings")
    embedding = models.BinaryField()
    face_index = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["photo"])
        ]


class AttendeeGallery(UUIDPkField):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="my_event_gallery"
    )
    photo_link = models.ForeignKey(
        EventPhoto,
        on_delete=models.CASCADE,
        related_name="attendee_saves"
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="attendee_galleries"
    )

    class Meta:
        unique_together = ("user", "photo_link")