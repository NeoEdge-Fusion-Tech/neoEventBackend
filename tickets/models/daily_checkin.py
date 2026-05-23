# tickets/models/daily_checkin.py
from django.db import models
from core.models import UUIDPkField

class DailyCheckIn(UUIDPkField):
    registration = models.ForeignKey(
        "tickets.EventRegistration",
        on_delete=models.CASCADE,
        related_name="daily_checkins"
    )
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    device_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ("registration", "date")
        ordering = ["-date", "-time"]
