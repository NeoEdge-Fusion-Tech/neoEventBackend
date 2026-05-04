import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

# Get an instance of a logger
logger = logging.getLogger(__name__)

def send_welcome_email(attendee_instance):
    """
    Handles the construction and sending of the welcome email using an HTML template.
    """
    subject = f"You're In! Welcome to {attendee_instance.full_name or 'the Event'}"
    
    # Context to pass to the HTML template
    context = {
        "attendee": attendee_instance,
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@neoevents.com")
    }
    
    try:
        # Render the HTML version
        html_message = render_to_string("emails/accounts/welcome_email.html", context)
        # Create a plain-text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        
        recipient_list = [attendee_instance.guest_email]
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Successfully sent welcome email to {attendee_instance.guest_email}")
        return True
        
    except Exception as e:
        logger.error(
            f"Failed to send welcome email to {attendee_instance.guest_email}. "
            f"Error: {str(e)}", 
            exc_info=True  # This captures the full stack trace in your logs
        )
        return False
    

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

    html_message = render_to_string("accounts/emails/password_reset.html", context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject="Reset your NeoEvent password",
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    
    