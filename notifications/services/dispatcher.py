import logging
from typing import List, Dict, Any
from .email_backend import EmailNotificationBackend
from .sms_backend import SMSNotificationBackend

logger = logging.getLogger(__name__)

class NotificationDispatcher:
    """
    Central service to dispatch notifications across multiple channels.
    """
    
    def __init__(self):
        self.backends = {
            'email': EmailNotificationBackend(),
            'sms': SMSNotificationBackend(),
            # Additional channels like 'push' can be registered here.
        }

    def send(self, channels: List[str], recipient_data: Dict[str, str], subject: str, template_name: str, context: Dict[str, Any], **kwargs):
        """
        Dispatches the notification to the specified channels.
        
        Args:
            channels (list): List of channels to use (e.g., ['email', 'sms'])
            recipient_data (dict): Dictionary mapping channels to recipient addresses (e.g., {'email': 'user@ex.com', 'sms': '+123456789'})
            subject (str): The subject of the notification.
            template_name (str): The template path.
            context (dict): The template context.
            **kwargs: Extra args (e.g., attachments).
        """
        results = {}
        
        for channel in channels:
            backend = self.backends.get(channel)
            if not backend:
                logger.warning(f"Notification channel '{channel}' is not supported.")
                results[channel] = False
                continue
                
            recipient = recipient_data.get(channel)
            if not recipient:
                logger.warning(f"No recipient address provided for channel '{channel}'. Skipping.")
                results[channel] = False
                continue
                
            success = backend.send(
                recipient=recipient, 
                subject=subject, 
                template_name=template_name, 
                context=context, 
                **kwargs
            )
            results[channel] = success
            
        return results

# Singleton instance for easy importing
notify = NotificationDispatcher()
