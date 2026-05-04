# models/event.py
import uuid

from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone


class Event(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_events"
    )

    title = models.CharField(max_length=255)

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    description = models.TextField()

    venue_name = models.CharField(max_length=255)

    venue_address = models.TextField()

    start_date = models.DateTimeField()

    end_date = models.DateTimeField()

    registration_deadline = models.DateTimeField()

    banner_image = models.ImageField(
        upload_to="event_banners/",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )

    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["owner"]),
            models.Index(fields=["slug"]),
        ]

    from uuid import uuid4
    def save(self, *args, **kwargs):

        if not self.slug:
            base_slug = slugify(self.title)
            unique_id = str(uuid4())[:8]

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


class EventVendor(models.Model):

    class VendorRole(models.TextChoices):
        PHOTOGRAPHER = "PHOTOGRAPHER", "Photographer"
        VIDEOGRAPHER = "VIDEOGRAPHER", "Videographer"
        PLANNER = "PLANNER", "Planner"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="vendors"
    )

    vendor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_assignments"
    )

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

    class Meta:
        unique_together = ("event", "vendor", "role")

    def __str__(self):
        return f"{self.vendor.username} -> {self.event.title}"
    
    
    # import uuid
# from django.db import models
# from django.conf import settings
# from django.utils import timezone

# class Event(models.Model):
#     STATUS_CHOICES = (
#         ('DRAFT', 'Draft'),
#         ('ACTIVE', 'Active (Ongoing)'),
#         ('COMPLETED', 'Completed'),
#         ('CANCELLED', 'Cancelled'),
#     )
    
#     owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_events')
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     start_date = models.DateTimeField()
#     end_date = models.DateTimeField(null=True, blank=True)
#     location = models.CharField(max_length=255)
#     registration_deadline = models.DateTimeField()
    
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
#     is_paid = models.BooleanField(default=False)
#     price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
#     banner_image = models.ImageField(upload_to='event_banners/')
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     @property
#     def is_currently_holding(self):
#         now = timezone.now()
#         if self.end_date:
#             return self.start_date <= now <= self.end_date
#         # Fallback for single-day events without explicit end time: 
#         # consider active until end of the start day
#         return self.start_date <= now <= self.start_date.replace(hour=23, minute=59, second=59)
        
#     def __str__(self):
#         return self.title


# class EventCategory(models.Model):
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_categories')
#     category = models.CharField(max_length=255,blank=True, null=True)
#     price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     is_free = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
    

# class EventPhotographer(models.Model):
#     event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_photographers')
#     photographer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_events')
#     email = models.EmailField(null=True, blank=True)
#     unique_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
#     invitation_sent = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     def __str__(self):
#         return f"Photographer for {self.event.title} ({self.email or self.photographer.username})"
