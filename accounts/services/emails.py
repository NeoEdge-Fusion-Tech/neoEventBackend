import logging
from django.conf import settings
from notifications.services.dispatcher import notify

logger = logging.getLogger(__name__)

def send_welcome_email(attendee_instance):
    """
    Handles the construction and sending of the welcome email using an HTML template.
    """
    subject = "Welcome to NeoEvent!"
    
    context = {
        "attendee": attendee_instance,
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@neoevents.com")
    }
    
    results = notify.send(
        channels=['email'],
        recipient_data={'email': attendee_instance.email},
        subject=subject,
        template_name="emails/accounts/welcome_email.html",
        context=context
    )
    return results.get('email', False)


def send_password_reset_email(user, reset_link: str) -> None:
    """
    Send a password-reset email to the given user.
    """
    expiry_seconds = getattr(settings, "PASSWORD_RESET_TIMEOUT", 3600)
    expiry_hours = expiry_seconds // 3600

    context = {
        "user": user,
        "reset_link": reset_link,
        "expiry_hours": expiry_hours,
        "platform_name": "NeoEvent",
    }

    notify.send(
        channels=['email'],
        recipient_data={'email': user.email},
        subject="Reset your NeoEvent password",
        template_name="emails/accounts/password_reset.html",
        context=context
    )


def send_otp_email(user, otp_code: str) -> bool:
    """
    Sends the 6-digit OTP email to the user for registration verification.
    """
    subject = "Verify your email - NeoEvents"
    
    context = {
        "user": user,
        "otp": otp_code,
    }
    
    results = notify.send(
        channels=['email'],
        recipient_data={'email': user.email},
        subject=subject,
        template_name="emails/accounts/verify_email.html",
        context=context
    )
    return results.get('email', False)