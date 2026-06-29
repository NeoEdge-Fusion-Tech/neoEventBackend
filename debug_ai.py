import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from photos.models import Photo, UserPhoto
from accounts.models import BiometricIdentity, User

print("All Photos:")
for p in Photo.objects.all():
    print(f"- Photo {p.id}: {p.ai_status}")
    
print("\nUserPhotos:")
for up in UserPhoto.objects.all():
    print(f"- UserPhoto {up.id}, photo_id={up.photo_id}, user_id={up.user_id}")

print("\nBiometricIdentities:")
for bio in BiometricIdentity.objects.all():
    print(f"- Bio {bio.id}: email={bio.email}, user_id={bio.user_id}, has_encoding={bio.face_encoding is not None}")

