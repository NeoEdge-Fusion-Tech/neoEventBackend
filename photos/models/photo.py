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


    class Meta:

        ordering = ["-uploaded_at"]

        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["uploaded_by"]),
            models.Index(fields=["uploaded_at"]),
        ]

    def __str__(self):

        return f"{self.event.title} - {self.uploaded_by.username}"
    