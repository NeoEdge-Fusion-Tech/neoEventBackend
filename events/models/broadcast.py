from django.db import models
from core.models import UUIDPkField
from .event import Event

class BroadcastMessage(UUIDPkField):
    class RecipientType(models.TextChoices):
        ALL = "ALL", "All Attendees"
        CONFIRMED = "CONFIRMED", "Confirmed Only"
        CHECKED_IN = "CHECKED_IN", "Checked In Only"

    class ChannelChoices(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"
        WHATSAPP = "WHATSAPP", "WhatsApp"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="broadcasts")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    recipient_type = models.CharField(max_length=20, choices=RecipientType.choices, default=RecipientType.ALL)
    channel = models.CharField(max_length=20, choices=ChannelChoices.choices, default=ChannelChoices.EMAIL)
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.subject} ({self.event.title})"
