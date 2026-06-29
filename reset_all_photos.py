import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from photos.models import Photo, UserPhoto

# Delete all mapping records so we start fresh
deleted_count, _ = UserPhoto.objects.all().delete()
print(f"Deleted {deleted_count} UserPhoto mapping records.")

# Reset all photos to PENDING
updated_count = Photo.objects.exclude(ai_status='PENDING').update(ai_status='PENDING')
print(f"Reset {updated_count} photos to PENDING.")

print("All AI processing data has been completely reset!")
