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
        # Read via the storage abstraction (not `.path`) so this works for
        # remote backends like Cloudinary/S3, not just local filesystem storage.
        with registration.qr_code.open("rb") as qr_file:
            qr_content = qr_file.read()
        attachments.append((f"{registration.registration_code}.png", qr_content, "image/png"))

    notify.send(
        channels=['email'],
        recipient_data={'email': attendee_email},
        subject=subject,
        template_name="emails/tickets/registration_confirmation.html",
        context=context,
        attachments=attachments
    )
