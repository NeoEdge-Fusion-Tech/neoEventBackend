from django.conf import settings
from .base import PaymentProvider
from .paystack import PaystackProvider

def get_payment_provider() -> PaymentProvider:
    gateway_name = getattr(settings, 'PAYMENT_GATEWAY', 'paystack').lower()
    
    if gateway_name == 'paystack':
        return PaystackProvider()
    
    raise ValueError(f"Unsupported payment gateway: {gateway_name}")
