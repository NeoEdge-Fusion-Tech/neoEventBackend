import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import AttendeeProfile, BiometricIdentity

User = get_user_model()

print("Backfilling AttendeeProfile users...")
for attendee in AttendeeProfile.objects.filter(user__isnull=True):
    parts = attendee.full_name.split(' ') if attendee.full_name else []
    first_name = parts[0] if len(parts) > 0 else ''
    last_name = parts[1] if len(parts) > 1 else ''
    
    user, created = User.objects.get_or_create(email=attendee.email, defaults={
        'username': attendee.email,
        'first_name': first_name,
        'last_name': last_name,
        'phone_number': attendee.phone_number,
        'role': 'ATTENDEE',
        'is_active': True
    })
    if created:
        user.set_unusable_password()
        user.save()
        print(f"Created user for {attendee.email}")
    
    attendee.user = user
    attendee.save()

print("Backfilling BiometricIdentity users...")
for bio in BiometricIdentity.objects.filter(user__isnull=True):
    user = User.objects.filter(email=bio.email).first()
    if user:
        bio.user = user
        bio.save()
        print(f"Linked user to BiometricIdentity for {bio.email}")

print("Done!")
