# events/models/event.py
import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from core.models import UUIDPkField


class Event(UUIDPkField):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="owned_events")
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    venue_name = models.CharField(max_length=255)
    venue_address = models.TextField()
    country = models.CharField(max_length=100, null=True, blank=True)
    state_or_county = models.CharField(max_length=100, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    number_of_days = models.PositiveIntegerField(default=1)
    registration_start = models.DateTimeField(default=timezone.now)
    registration_deadline = models.DateTimeField()
    max_participants = models.PositiveIntegerField(default=100)
    
    # to be changed to the cloud
    banner_image = models.ImageField(
        upload_to="event_banners/",
        null=True,
        blank=True,
        max_length=500,
    )
    banner_portrait = models.ImageField(
        upload_to="event_banners/",
        null=True,
        blank=True,
        max_length=500,
    )
    banner_video = models.FileField(
        upload_to="event_banners/",
        null=True,
        blank=True,
        max_length=500,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    is_public = models.BooleanField(default=True)
    currency = models.CharField(max_length=10, default="USD")
    badge_template = models.TextField(
        null=True, 
        blank=True,
        help_text="Custom HTML template for the badge. Use {fullname}, {ticket_id}, {ticket_type}, {qr_code} as placeholders."
    )
    attendees_notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["owner"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_id = str(uuid.uuid4())[:8]
            self.slug = f"{base_slug}-{unique_id}"
        super().save(*args, **kwargs)

    @property
    def is_live(self):
        now = timezone.now()
        return (
            self.status == self.Status.ACTIVE
            and self.start_date <= now <= self.end_date
        )

    @property
    def can_register(self):
        now = timezone.now()
        return (
            self.status in [self.Status.PUBLISHED, self.Status.ACTIVE]
            and now <= self.registration_deadline
        )

    def __str__(self):
        return self.title


