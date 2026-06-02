from abc import ABC, abstractmethod

class BaseNotificationBackend(ABC):
    """
    Abstract base class for all notification backends (Email, SMS, Push, etc.).
    """

    @abstractmethod
    def send(self, recipient, subject, template_name, context, **kwargs) -> bool:
        """
        Sends the notification.
        
        Args:
            recipient (str): The recipient address (email, phone number, etc.).
            subject (str): The subject or title of the notification.
            template_name (str): The path or identifier for the template.
            context (dict): The context data to render the template.
            **kwargs: Any additional backend-specific arguments.
            
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        pass
