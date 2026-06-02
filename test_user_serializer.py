import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User, EventOwnerProfile
from accounts.serializers.user import UserSerializer

user = User.objects.create(email="testowner2@example.com", username="testowner2", role="OWNER", first_name="RealFirst", last_name="RealLast")
profile = EventOwnerProfile.objects.create(user=user, organisation_name="My Org 2")

serializer = UserSerializer(user)
print("USER SERIALIZER DATA:", serializer.data)

user.delete()
