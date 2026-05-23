# events/models/vendor.py
import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from .event import Event
from core.models import UUIDPkField


class EventVendor(UUIDPkField):
    class VendorRole(models.TextChoices):
        PHOTOGRAPHER = "PHOTOGRAPHER", "Photographer"
        VIDEOGRAPHER = "VIDEOGRAPHER", "Videographer"
        PLANNER = "PLANNER", "Planner"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="vendors")
    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_assignments",
        null=True, blank=True
    )
    invited_email = models.EmailField(null=True, blank=True)
    invited_name = models.CharField(max_length=150, null=True, blank=True)
    role = models.CharField(
        max_length=30,
        choices=VendorRole.choices
    )
    invitation_code = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    is_confirmed = models.BooleanField(default=False)
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("event", "vendor", "role")

    def __str__(self):
        if self.vendor:
            return f"{self.vendor.username} -> {self.event.title}"
        return f"{self.invited_email} -> {self.event.title}"
