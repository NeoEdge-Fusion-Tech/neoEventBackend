from django.db import models
from django.contrib.auth import get_user_model
from core.models import UUIDPkField

User = get_user_model()

class ValidatorProfile(UUIDPkField):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="validator_profile")
    device_name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.device_name}"
