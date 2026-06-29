import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from photos.models import Photo, UserPhoto

# Find all photos that claim to be mapped but have no UserPhoto
mapped_photos = Photo.objects.filter(ai_status='MAPPED_TO_USERS')
fixed_count = 0

for p in mapped_photos:
    if not UserPhoto.objects.filter(photo_id=p.id).exists():
        p.ai_status = 'PENDING'
        p.save()
        fixed_count += 1

print(f"Reset {fixed_count} photos to PENDING.")
