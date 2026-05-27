import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)

def send_vendor_invitation_email(event_vendor):
    """Sends HTML invitation to a Vendor from an Event Owner."""
    event = event_vendor.event
    vendor = event_vendor.vendor # This assumes vendor is a User object

    subject = f"Invitation: You've been invited to '{event.title}'"
    
    recipient_email = vendor.email if vendor else event_vendor.invited_email
    vendor_name = vendor.first_name or vendor.username if vendor else event_vendor.invited_name
    
    context = {
        "event_vendor": event_vendor,
        "event": event,
        "vendor": vendor,
        "vendor_name": vendor_name,
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@neoevents.com")
    }

    try:
        html_message = render_to_string("emails/events/vendor_invitation.html", context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Vendor invitation sent to {recipient_email} for event {event.id}")
    except Exception as e:
        logger.error(f"Failed to send vendor invitation to {recipient_email}: {str(e)}", exc_info=True)


def send_vendor_acceptance_email(event_vendor):
    """Notifies the Event Owner that a Vendor has accepted."""
    event = event_vendor.event
    owner = event.owner

    subject = f"Accepted: Vendor joined '{event.title}'"
    context = {
        "event_vendor": event_vendor,
        "event": event,
        "owner": owner,
    }

    try:
        html_message = render_to_string("emails/events/vendor_acceptance.html", context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[owner.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Acceptance notification sent to owner {owner.email} for vendor {event_vendor.vendor.username}")
    except Exception as e:
        logger.error(f"Failed to send acceptance email to {owner.email}: {str(e)}", exc_info=True)

        




# from django.conf import settings
# from django.core.mail import send_mail


# def send_vendor_invitation_email(event_vendor):

#     event = event_vendor.event
#     vendor = event_vendor.vendor

#     subject = f"You've been invited to '{event.title}'"

#     message = (
#         f"Hello {vendor.first_name or vendor.username},\n\n"
#         f"You have been invited as a "
#         f"{event_vendor.get_role_display()} "
#         f"for the event '{event.title}'.\n\n"
#         f"Invitation Code:\n"
#         f"{event_vendor.invitation_code}\n\n"
#         f"Please log in to your account to accept or decline "
#         f"this invitation.\n\n"
#         f"Event Venue: {event.venue_name}\n"
#         f"Start Date: {event.start_date}\n\n"
#         f"Thank you."
#     )

#     send_mail(
#         subject=subject,
#         message=message,
#         from_email=settings.DEFAULT_FROM_EMAIL,
#         recipient_list=[vendor.email],
#         fail_silently=False,
#     )


# def send_vendor_acceptance_email(event_vendor):

#     event = event_vendor.event

#     subject = (
#         f"Vendor accepted invitation for '{event.title}'"
#     )

#     message = (
#         f"Hello {event.owner.first_name or event.owner.username},\n\n"
#         f"{event_vendor.vendor.username} has accepted "
#         f"the invitation as "
#         f"{event_vendor.get_role_display()}.\n\n"
#         f"Event: {event.title}\n"
#         f"Venue: {event.venue_name}\n\n"
#         f"Regards,\n"
#         f"Neo Events"
#     )

#     send_mail(
#         subject=subject,
#         message=message,
#         from_email=settings.DEFAULT_FROM_EMAIL,
#         recipient_list=[event.owner.email],
#         fail_silently=False,
#     )

