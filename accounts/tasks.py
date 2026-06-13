import requests
from celery import shared_task
from .models.biometrics import BiometricIdentity

from decouple import config

FASTAPI_REFERENCE_URL = config("FASTAPI_PROCESS_REFERENCE_URL", default="http://fastapi_prod_host:8002/process-reference")

@shared_task
def process_biometric_image(email, image_url, user_id=None):
    """
    Background task to process a biometric reference image.
    It triggers the FastAPI service to extract the 512D face encoding using InsightFace.
    """
    try:
        # We first ensure the BiometricIdentity record exists so FastAPI can update it
        defaults = {}
        if user_id is not None:
            defaults['user_id'] = user_id
            
        BiometricIdentity.objects.get_or_create(
            email=email,
            defaults=defaults
        )
        
        # Send the request to FastAPI. FastAPI fetches the image directly from the URL.
        payload = {
            'email': email,
            'image_url': str(image_url),
            'user_id': str(user_id) if user_id else None
        }
        
        response = requests.post(FASTAPI_REFERENCE_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"Triggered 512D reference extraction for {email}")
            return True
        else:
            print(f"Failed to trigger reference extraction for {email}: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error triggering reference extraction for {email}: {e}")
        return False
