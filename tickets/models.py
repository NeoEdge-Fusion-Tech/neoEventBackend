# ticket/models.py
from django.db import models
from django.conf import settings
import uuid

class TicketType(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="ticket_types"
    )

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

    quantity = models.PositiveIntegerField()

    sold_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def remaining(self):
        return self.quantity - self.sold_count
    

class EventRegistration(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CHECKED_IN = "CHECKED_IN", "Checked In"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

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

    qr_code = models.ImageField(
        upload_to="qr_codes/",
        null=True,
        blank=True
    )

    checked_in = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED
    )

    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "attendee")
        