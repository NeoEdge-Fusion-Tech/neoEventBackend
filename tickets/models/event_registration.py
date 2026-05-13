# tickets/models/event_registration.py
from django.db import models
import uuid 
from .ticket_type import TicketType   
from core.models import UUIDPkField


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
        related_name="registrations"
    )

    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    registration_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    qr_code = models.ImageField(upload_to="qr_codes/", null=True, blank=True)
    checked_in = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    registered_at = models.DateTimeField(auto_now_add=True)

    # checked_in_at = models.DateTimeField(
    #     null=True,
    #     blank=True
    # )
    
    class Meta:
        unique_together = ("event", "attendee")

        indexes = [
            models.Index(fields=["event"]),
            models.Index(fields=["registration_code"]),
            models.Index(fields=["status"]),
        ]
