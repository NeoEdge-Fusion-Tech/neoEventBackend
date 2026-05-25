from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def send_registration_confirmation_email(registration):

    attendee_email = registration.attendee.email

    subject = f"Your Ticket for {registration.event.title}"

    context = {
        "registration": registration,
        "event": registration.event,
        "attendee": registration.attendee,
    }

    html_message = render_to_string(
        "emails/tickets/registration_confirmation.html",
        context,
    )

    email = EmailMessage(
        subject=subject,
        body=html_message,
        to=[attendee_email],
    )

    email.content_subtype = "html"

    # Attach QR Code
    if registration.qr_code:
        email.attach_file(registration.qr_code.path)

    try:
        email.send(fail_silently=True)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send registration confirmation email to {attendee_email}: {e}")
