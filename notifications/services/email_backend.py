import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .base import BaseNotificationBackend

logger = logging.getLogger(__name__)

class EmailNotificationBackend(BaseNotificationBackend):
    """
    Handles sending notifications via Email using Django's core mail module.
    """

    def send(self, recipient, subject, template_name, context, attachments=None, **kwargs) -> bool:
        try:
            # Add global settings to context
            context['frontend_url'] = getattr(settings, 'FRONTEND_URL', 'https://neoevents.com')
            
            # Render HTML and Plain Text versions
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@neoevents.com')
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=from_email,
                to=[recipient]
            )
            msg.attach_alternative(html_message, "text/html")
            
            # Handle attachments (e.g., QR Codes for tickets)
            if attachments:
                for attachment in attachments:
                    if isinstance(attachment, (tuple, list)):
                        filename, content, mimetype = attachment
                        msg.attach(filename, content, mimetype)
                    else:
                        # Backward-compatible: a local filesystem path
                        msg.attach_file(attachment)
                    
            msg.send(fail_silently=False)
            logger.info(f"Successfully sent email '{subject}' to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email '{subject}' to {recipient}: {e}", exc_info=True)
            return False
