import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from photos.models import UserPhoto, Photo
from accounts.models import User, BiometricIdentity

print("UserPhotos:")
for up in UserPhoto.objects.all():
    print(f"Photo: {up.photo_id}, User: {up.user.email} (ID: {up.user.id})")

print("\nUsers with same email as BiometricIdentity:")
for bio in BiometricIdentity.objects.all():
    print(f"Bio Email: {bio.email}, Bio UserID: {bio.user_id}")
    users = User.objects.filter(email=bio.email)
    for u in users:
        print(f"  Found User: {u.email} (ID: {u.id})")
