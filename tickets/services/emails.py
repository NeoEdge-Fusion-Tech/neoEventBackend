import logging
from notifications.services.dispatcher import notify

logger = logging.getLogger(__name__)

def send_registration_confirmation_email(registration):

    attendee_email = registration.attendee.email
    subject = f"Your Ticket for {registration.event.title}"

    context = {
        "registration": registration,
        "event": registration.event,
        "attendee": registration.attendee,
    }

    attachments = []
    if registration.qr_code:
        attachments.append(registration.qr_code.path)

    notify.send(
        channels=['email'],
        recipient_data={'email': attendee_email},
        subject=subject,
        template_name="emails/tickets/registration_confirmation.html",
        context=context,
        attachments=attachments
    )
