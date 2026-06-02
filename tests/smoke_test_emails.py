import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Add parent directory to path so it can find the 'core' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from notifications.services.dispatcher import notify

def send_test_email(subject, template_name, context, recipient):
    result = notify.send(
        channels=['email'],
        recipient_data={'email': recipient},
        subject=subject,
        template_name=template_name,
        context=context
    )
    if result.get('email'):
        print(f"✅ Successfully sent '{subject}' to {recipient} via NotificationService")
    else:
        print(f"❌ Failed to send '{subject}' to {recipient}")

def run_smoke_test(recipient_email):
    print(f"Starting Email Smoke Test for: {recipient_email}...")
    
    class DummyUser:
        first_name = "Sunday"
        username = "sunnex"
        email = recipient_email
        full_name = "Sunday Ajayi"
        
    class DummyEvent:
        title = "NeoEvents Tech Summit 2026"
        venue_name = "Eko Convention Center"
        venue_address = "Victoria Island, Lagos, Nigeria"
        start_date = timezone.now() + timedelta(days=7)
        end_date = timezone.now() + timedelta(days=8)
        owner = DummyUser()
        
    class DummyEventVendor:
        vendor = DummyUser()
        role = "photographer"
        get_role_display = lambda self: "Photographer"
        invitation_code = "NEO-7X9P2M"
        
    class DummyRegistration:
        registration_code = "REG-99XYZ2"

    user = DummyUser()
    event = DummyEvent()
    event_vendor = DummyEventVendor()
    registration = DummyRegistration()
    user = DummyUser()
    event = DummyEvent()
    event_vendor = DummyEventVendor()
    
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

    # Test 1: Gallery Ready Email
    print("\nSending 1/6: Gallery Ready Email...")
    send_test_email(
        subject=f"Your Photos from {event.title} are Ready!",
        template_name="emails/gallery_ready.html",
        context={
            "user": user,
            "event": event,
            "gallery_url": f"{frontend_url}/events/123/gallery?category=personal",
            "frontend_url": frontend_url
        },
        recipient=recipient_email
    )

    # Test 2: Vendor Invitation Email
    print("Sending 2/6: Vendor Invitation Email...")
    send_test_email(
        subject=f"You've Been Invited to {event.title} as a {event_vendor.get_role_display()}",
        template_name="emails/events/vendor_invitation.html",
        context={
            "vendor_name": user.first_name,
            "event_vendor": event_vendor,
            "event": event,
            "settings": settings
        },
        recipient=recipient_email
    )

    # Test 3: Verify Email
    print("Sending 3/6: Verify Email OTP...")
    send_test_email(
        subject="Verify your NeoEvents Account",
        template_name="emails/accounts/verify_email.html",
        context={
            "user": user,
            "otp": "482051"
        },
        recipient=recipient_email
    )

    # Test 4: Password Reset Email
    print("Sending 4/6: Password Reset Email...")
    send_test_email(
        subject="Reset your NeoEvent password",
        template_name="emails/accounts/password_reset.html",
        context={
            "user": user,
            "expiry_hours": 24,
            "reset_link": f"{frontend_url}/reset-password?token=mock_token_123"
        },
        recipient=recipient_email
    )

    # Test 5: Welcome Email
    print("Sending 5/6: Welcome Email...")
    send_test_email(
        subject="Welcome to NeoEvents! 🎉",
        template_name="emails/accounts/welcome_email.html",
        context={
            "attendee": user,
            "settings": settings,
            "support_email": "support@neoevents.co"
        },
        recipient=recipient_email
    )

    # Test 6: Registration Confirmation
    print("Sending 6/6: Registration Confirmation Email...")
    send_test_email(
        subject=f"Registration Confirmed for {event.title}",
        template_name="emails/tickets/registration_confirmation.html",
        context={
            "attendee": user,
            "event": event,
            "registration": registration
        },
        recipient=recipient_email
    )
    
    print("\n🎉 Smoke Test Complete! All 6 templates were dispatched. Please check your inbox.")

if __name__ == "__main__":
    run_smoke_test("sunnexajayi@gmail.com")
