import logging
from .base import BaseNotificationBackend

logger = logging.getLogger(__name__)

class SMSNotificationBackend(BaseNotificationBackend):
    """
    Handles sending notifications via SMS.
    Currently a placeholder. Can be integrated with Twilio, AWS SNS, Termii, etc.
    """

    def send(self, recipient, subject, template_name, context, **kwargs) -> bool:
        try:
            # Placeholder: In the future, render a short text template here
            # and dispatch via SMS provider API.
            logger.info(f"SMS Mock Sent to {recipient} - {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {recipient}: {e}", exc_info=True)
            return False
