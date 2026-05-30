import requests
from celery import shared_task
from .models.biometrics import BiometricIdentity

FASTAPI_REFERENCE_URL = "http://localhost:8002/process-reference"

@shared_task
def process_biometric_image(email, image_path, user_id=None):
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
        
        # Send the request to FastAPI. FastAPI reads the image directly from MEDIA_ROOT.
        payload = {
            'email': email,
            'image_path': str(image_path)
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
