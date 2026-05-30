from django.db.models.signals import post_save
from django.dispatch import receiver
from .models.photo import Photo
from .tasks import extract_faces_from_photos

@receiver(post_save, sender=Photo)
def trigger_photo_processing(sender, instance, created, **kwargs):
    if created:
        # Offload AI extraction to Celery background worker
        extract_faces_from_photos.delay([instance.id])
        
