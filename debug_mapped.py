import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from photos.models import UserPhoto, Photo
from accounts.models import User

print("Photos with MAPPED_TO_USERS:")
for p in Photo.objects.filter(ai_status='MAPPED_TO_USERS'):
    print(f"- Photo {p.id}, event_id={p.event_id}")

print("\nUserPhotos:")
for up in UserPhoto.objects.all():
    print(f"- UserPhoto {up.id}, photo_id={up.photo_id}, user_id={up.user_id}")
    u = User.objects.filter(id=up.user_id).first()
    print(f"  User exists in DB? {u is not None}")

