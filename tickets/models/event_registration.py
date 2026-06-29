# tickets/models/event_registration.py
from django.db import models
import uuid 
from .ticket_type import TicketType   
from core.models import UUIDPkField
from core.utils.codes import generate_registration_code


class EventRegistration(UUIDPkField):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CHECKED_IN = "CHECKED_IN", "Checked In"
        CANCELLED = "CANCELLED", "Cancelled"


    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="registrations"
    )

    attendee = models.ForeignKey(
        "accounts.AttendeeProfile",
        on_delete=models.CASCADE,
        related_name="registrations",
        null=True,
        blank=True
    )

    attendee_name = models.CharField(max_length=255, null=True, blank=True)
    attendee_email = models.EmailField(null=True, blank=True)
    group_name = models.CharField(max_length=255, null=True, blank=True)
    group_code = models.UUIDField(null=True, blank=True)

    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    registration_code = models.CharField(
        max_length=50,
        default=generate_registration_code,
        unique=True,
        editable=False
    )

    qr_code = models.ImageField(upload_to="qr_codes/", null=True, blank=True)
    checked_in = models.BooleanField(default=False)
    ai_consent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    registered_at = models.DateTimeField(auto_now_add=True)
    badge_print_count = models.PositiveIntegerField(default=0)
    last_badge_printed_at = models.DateTimeField(null=True, blank=True)

    # checked_in_at = models.DateTimeField(
    #     null=True,
    #     blank=True
    # )
    
    class Meta:
        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["registration_code"]),
            models.Index(fields=["status"]),
        ]
