from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AttendeeProfile
from .services.emails import send_welcome_email

@receiver(post_save, sender=AttendeeProfile)
def handle_new_registration_email(sender, instance, created, **kwargs):
    if created and instance.guest_email:
        send_welcome_email(instance)

