import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User, EventOwnerProfile
from accounts.serializers.profiles import EventOwnerProfileSerializer

user = User.objects.create(email="testowner@example.com", username="testowner", role="OWNER", first_name="OldFirst", last_name="OldLast")
profile = EventOwnerProfile.objects.create(user=user)

data = {
    "first_name": "NewFirst",
    "last_name": "NewLast",
    "organisation_name": "My Org"
}

serializer = EventOwnerProfileSerializer(profile, data=data, partial=True)
if serializer.is_valid():
    print("VALIDATED DATA:", serializer.validated_data)
    updated_profile = serializer.save()
    print("SAVED USER FIRST NAME:", updated_profile.user.first_name)
    print("SAVED USER LAST NAME:", updated_profile.user.last_name)
    print("SERIALIZER DATA:", serializer.data)
else:
    print("ERRORS:", serializer.errors)

user.delete()
