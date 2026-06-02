import os
import django
import sys

# Setup django environment
sys.path.append('/Users/sunday/Documents/Project/NeoEdge/neoEventv1/neoEventBackend')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print("USERS:")
for u in User.objects.all():
    print(f"Email: {u.email}, is_active: {u.is_active}, has_usable_password: {u.has_usable_password()}, onboarding_status: {u.onboarding_status}")
