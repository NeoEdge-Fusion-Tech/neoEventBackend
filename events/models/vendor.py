# events/models/vendor.py
import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from .event import Event
from core.models import UUIDPkField


def generate_invitation_code():
    import string, random
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class EventVendor(UUIDPkField):
    # We keep this as a reference or namespace for default roles
    class VendorRole(models.TextChoices):
        PHOTOGRAPHER = "PHOTOGRAPHER", "Photographer"
        VIDEOGRAPHER = "VIDEOGRAPHER", "Videographer"
        PLANNER = "PLANNER", "Planner"
        CATERER = "CATERER", "Caterer"
        DECORATOR = "DECORATOR", "Decorator"

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
    invited_phone = models.CharField(max_length=30, null=True, blank=True)
    role = models.CharField(
        max_length=50,
        choices=VendorRole.choices,
        default=VendorRole.PHOTOGRAPHER,
    )
    invitation_code = models.CharField(
        max_length=50,
        default=generate_invitation_code,
        editable=False,
        unique=True
    )
    is_confirmed = models.BooleanField(default=False)
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    media_public_showcase_allowed = models.BooleanField(
        default=False, 
        help_text="If true, the vendor can showcase media from this event on their public portfolio."
    )

    class Meta:
        unique_together = ("event", "vendor", "role")

    def __str__(self):
        if self.vendor:
            return f"{self.vendor.username} -> {self.event.title}"
        return f"{self.invited_email} -> {self.event.title}"

class InvitedEventMedia(UUIDPkField):
    event_vendor = models.ForeignKey(EventVendor, on_delete=models.CASCADE, related_name="uploaded_media")
    raw_image = models.ImageField(upload_to="invited_media/raw/")
    watermarked_image = models.ImageField(upload_to="invited_media/watermarked/", null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Media for {self.event_vendor}"

class VendorRating(UUIDPkField):
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_ratings")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="vendor_ratings")
    attendee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="given_vendor_ratings")
    rating = models.PositiveIntegerField(default=5) # 1 to 5
    review = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("vendor", "event", "attendee")

    def __str__(self):
        return f"{self.rating}/5 for {self.vendor.username} by {self.attendee.username}"
