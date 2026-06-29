import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from photos.models import Photo

p = Photo.objects.filter(id="5dcd1c00-cd87-49b9-b5ac-91a64dc8082e").first()
if p:
    p.ai_status = 'PENDING'
    p.save()
    print("Reset photo to PENDING.")

