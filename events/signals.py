from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import EventVendor

from .services.emails import (
    send_vendor_invitation_email,
    send_vendor_acceptance_email,
)


@receiver(post_save, sender=EventVendor)
def handle_vendor_invitation(sender, instance, created, **kwargs):

    if created:
        send_vendor_invitation_email(instance)


@receiver(pre_save, sender=EventVendor)
def track_acceptance_change(sender, instance, **kwargs):

    if not instance.pk:
        instance._was_confirmed = False
        return

    previous = EventVendor.objects.get(pk=instance.pk)

    instance._was_confirmed = previous.is_confirmed


@receiver(post_save, sender=EventVendor)
def handle_vendor_acceptance(sender, instance, created, **kwargs):

    if created:
        return

    if not getattr(instance, "_was_confirmed", False) and instance.is_confirmed:
        send_vendor_acceptance_email(instance)
