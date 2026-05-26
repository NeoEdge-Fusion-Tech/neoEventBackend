import requests
from django.conf import settings
from .base import PaymentProvider

class PaystackProvider(PaymentProvider):
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.base_url = "https://api.paystack.co"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def initialize_payment(self, amount: float, email: str, reference: str, **kwargs) -> dict:
        if not self.secret_key:
            raise ValueError("PAYSTACK_SECRET_KEY is not set or is empty in the environment.")
            
        url = f"{self.base_url}/transaction/initialize"
        # Paystack expects amount in kobo (base unit)
        amount_kobo = int(float(amount) * 100)
        
        payload = {
            "amount": amount_kobo,
            "email": email,
            "reference": reference,
        }
        
        if "callback_url" in kwargs:
            payload["callback_url"] = kwargs["callback_url"]
            
        response = requests.post(url, json=payload, headers=self._headers())
        response.raise_for_status()
        
        data = response.json()["data"]
        return {
            "authorization_url": data["authorization_url"],
            "reference": data["reference"],
            "raw_data": data
        }

    def verify_payment(self, reference: str) -> dict:
        url = f"{self.base_url}/transaction/verify/{reference}"
        
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        
        data = response.json()["data"]
        
        status_map = {
            "success": "success",
            "failed": "failed",
            "abandoned": "failed",
            "reversed": "failed"
        }
        
        # Convert amount back to main currency (e.g., NGN from kobo)
        amount = data.get("amount", 0) / 100.0
        
        return {
            "status": status_map.get(data.get("status", ""), "pending"),
            "amount": amount,
            "currency": data.get("currency", "NGN"),
            "raw_data": data
        }
