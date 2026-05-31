import random
import string
from django.utils import timezone
from ..services.emails import send_otp_email

def generate_and_send_otp(user):
    """
    Generates a 6-digit OTP, saves it to the user instance,
    and sends the OTP email.
    """
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    user.email_verification_otp = otp_code
    user.email_verification_otp_created_at = timezone.now()
    user.onboarding_status = user.OnboardingStatus.PENDING_EMAIL
    user.is_email_verified = False
    
    user.save(update_fields=[
        'email_verification_otp', 
        'email_verification_otp_created_at', 
        'onboarding_status',
        'is_email_verified'
    ])
    
    # Send the email (this can be offloaded to Celery/SQS if needed in the future)
    send_otp_email(user, otp_code)
