# models/profiles.py
from django.db import models
from django.conf import settings

class BaseProfile(models.Model):
    """Abstract base to avoid repeating timestamps and payout refs."""
    payout_account_ref = models.CharField(
        max_length=255,
        blank=True,
        help_text="Tokenised reference from the payment gateway."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class EventOwnerProfile(BaseProfile):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_profile",
    )
    organisation_name = models.CharField(max_length=255, blank=True)
    organisation_website = models.URLField(max_length=255, blank=True)
    organisation_logo = models.ImageField(upload_to="org_logos/", null=True, blank=True)
    
    business_registration_number = models.CharField(max_length=100, blank=True)
    is_business_verified = models.BooleanField(default=False)

    total_events_created = models.PositiveIntegerField(default=0)
    total_tickets_sold = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Owner: {self.organisation_name or self.user.username}"

class VendorProfile(BaseProfile):
    class VendorSubtype(models.TextChoices):
        PHOTOGRAPHER = "PHOTOGRAPHER", "Photographer"
        PLANNER = "PLANNER", "Event Planner"
        VIDEOGRAPHER = "VIDEOGRAPHER", "Videographer"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vendor_profile",
    )
    subtype = models.CharField(max_length=20, choices=VendorSubtype.choices)
    bio = models.TextField(max_length=500, blank=True)
    profile_image = models.ImageField(upload_to="vendor_profiles/", null=True, blank=True)
    
    service_title = models.CharField(max_length=255, blank=True)
    service_areas = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated list of locations served.")
    
    years_of_experience = models.PositiveSmallIntegerField(default=0)
    is_available_for_hire = models.BooleanField(default=True)

    base_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    rate_unit = models.CharField(max_length=20, default="per_event")
    
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Vendor: {self.user.username} ({self.subtype})"
    
    