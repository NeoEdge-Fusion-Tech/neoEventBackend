from django.db.models.signals import post_save

from django.dispatch import receiver

from .models.event_registration import EventRegistration

from .services.qr import generate_registration_qr

from .services.emails import (
    send_registration_confirmation_email,
)


@receiver(post_save, sender=EventRegistration)
def handle_registration_created(sender, instance, created, **kwargs):

    if not created:
        return

    # -------------------------------------------------
    # Generate QR
    # -------------------------------------------------

    generate_registration_qr(instance)

    instance.save(update_fields=["qr_code"])

    # -------------------------------------------------
    # Send Email
    # -------------------------------------------------

    send_registration_confirmation_email(instance)
