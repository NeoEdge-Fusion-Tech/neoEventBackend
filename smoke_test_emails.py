import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import AttendeeProfile
from accounts.services.emails import send_welcome_email, send_otp_email
from events.services.emails import send_vendor_invitation_email
from tickets.services.emails import send_registration_confirmation_email

User = get_user_model()

def run_smoke_test():
    test_email = 'sunnexajayi@gmail.com'
    print(f"Starting email smoke test for {test_email}...")
    
    # 1. Create a dummy user/attendee
    user, created = User.objects.get_or_create(
        email=test_email,
        defaults={
            'username': 'sunnexajayi',
            'first_name': 'Sunday',
            'last_name': 'Ajayi',
            'role': User.Role.ATTENDEE
        }
    )
    
    attendee, created = AttendeeProfile.objects.get_or_create(
        user=user,
        email=test_email,
        defaults={
            'full_name': 'Sunday Ajayi',
        }
    )
    
    # 2. Test Welcome Email
    try:
        send_welcome_email(attendee)
        print("✅ Welcome Email sent")
    except Exception as e:
        print(f"❌ Welcome Email failed: {e}")
        
    # 3. Test OTP Email
    try:
        user.email_verification_otp = '123456'
        user.save()
        send_otp_email(user, '123456')
        print("✅ OTP Email sent")
    except Exception as e:
        print(f"❌ OTP Email failed: {e}")

    # 4. Test Vendor Invitation Email
    # We need a dummy event and event_vendor link
    event = None
    try:
        from events.models import Event, EventVendor
        from django.utils import timezone
        import datetime
        event, created = Event.objects.get_or_create(
            title="Smoke Test Event",
            defaults={
                'owner': user,
                'start_date': timezone.now() + datetime.timedelta(days=1),
                'end_date': timezone.now() + datetime.timedelta(days=2),
                'registration_deadline': timezone.now() + datetime.timedelta(days=1)
            }
        )
        event_vendor, created = EventVendor.objects.get_or_create(
            event=event,
            invited_email=test_email,
        )
        send_vendor_invitation_email(event_vendor)
        print("✅ Vendor Invitation Email sent")
    except Exception as e:
        print(f"❌ Vendor Invitation Email failed: {e}")

    # 5. Test Ticket Registration Confirmation Email
    try:
        if event is None:
            raise Exception("Cannot test tickets because event creation failed")
            
        from tickets.models import TicketType, EventRegistration
        import uuid
        ticket, created = TicketType.objects.get_or_create(
            event=event,
            name="VIP Ticket",
            defaults={
                'price': 100.00,
                'quantity': 100
            }
        )
        registration, created = EventRegistration.objects.get_or_create(
            attendee=attendee,
            event=event,
            ticket_type=ticket,
            defaults={
                'registration_code': str(uuid.uuid4())[:8].upper()
            }
        )
        send_registration_confirmation_email(registration)
        print("✅ Ticket Registration Confirmation Email sent")
    except Exception as e:
        print(f"❌ Ticket Registration Confirmation Email failed: {e}")
        
    # Test Password Reset Email
    try:
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.template.loader import render_to_string
        from django.core.mail import send_mail
        from django.conf import settings
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"http://localhost:3000/reset-password?uid={uid}&token={token}"
        
        html_content = render_to_string('emails/accounts/password_reset.html', {
            'user': user,
            'reset_link': reset_link,
            'company_name': 'NeoEvent',
        })
        send_mail(
            subject="Password Reset - NeoEvent",
            message="",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        print("✅ Password Reset Email sent")
    except Exception as e:
        print(f"❌ Password Reset Email failed: {e}")


if __name__ == '__main__':
    run_smoke_test()
