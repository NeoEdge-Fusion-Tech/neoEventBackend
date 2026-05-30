import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "neoEventBackend.settings")
django.setup()

from django.contrib.auth import get_user_model
from accounts.serializers.user import UserSerializer

User = get_user_model()
user = User.objects.filter(username="p_media_vendor").first()
if user:
    print(UserSerializer(user).data)
else:
    print("User not found")
