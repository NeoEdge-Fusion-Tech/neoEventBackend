from django.db import models
from django.conf import settings
from pgvector.django import VectorField

class BiometricIdentity(models.Model):
    email = models.EmailField(unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    face_encoding = VectorField(dimensions=512, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Biometric Data for {self.email}"
