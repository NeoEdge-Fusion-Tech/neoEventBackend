import logging
from django.conf import settings
from notifications.services.dispatcher import notify

logger = logging.getLogger(__name__)

def send_vendor_invitation_email(event_vendor):
    """Sends HTML invitation to a Vendor from an Event Owner."""
    event = event_vendor.event
    vendor = event_vendor.vendor

    subject = f"You've Been Invited to '{event.title}' as a {event_vendor.get_role_display()}"
    
    recipient_email = vendor.email if vendor else event_vendor.invited_email
    vendor_name = (vendor.first_name or vendor.username) if vendor else event_vendor.invited_name

    if not recipient_email:
        logger.error(
            f"[Vendor Invite] Cannot send email for EventVendor {event_vendor.pk} "
            f"on Event '{event.title}': no recipient email found. "
            f"vendor={vendor}, invited_email={event_vendor.invited_email}"
        )
        return

    context = {
        "event_vendor": event_vendor,
        "event": event,
        "vendor": vendor,
        "vendor_name": vendor_name,
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@neoevents.com")
    }

    results = notify.send(
        channels=['email'],
        recipient_data={'email': recipient_email},
        subject=subject,
        template_name="emails/events/vendor_invitation.html",
        context=context
    )

    if results.get('email'):
        logger.info(f"[Vendor Invite] Email sent to {recipient_email} for event '{event.title}'")
    else:
        logger.error(f"[Vendor Invite] Failed to send invitation email to {recipient_email} for event '{event.title}'")
