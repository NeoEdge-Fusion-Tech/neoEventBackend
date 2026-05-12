from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Photo
from .tasks import process_photo_ai

@receiver(post_save, sender=Photo)
def trigger_photo_processing(sender, instance, created, **kwargs):
    if created:
        # Offload AI processing to Celery background worker
        process_photo_ai.delay(instance.id)
        
