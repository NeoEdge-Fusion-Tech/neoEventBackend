import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from accounts.models import User, EventOwnerProfile
from rest_framework_simplejwt.tokens import RefreshToken

# Create a test user
user = User.objects.create_user(email="testowner5@example.com", username="testowner5", password="testpassword123", role="OWNER")
profile, _ = EventOwnerProfile.objects.get_or_create(user=user)

# Get token
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

# Make PATCH request to update profile
client = Client()
headers = {
    'HTTP_AUTHORIZATION': f'Bearer {access_token}',
}
data = {
    'first_name': 'UpdatedFirst',
    'last_name': 'UpdatedLast',
    'organisation_name': 'My New Org'
}

print("SENDING DATA:", data)
response = client.patch('/api/account/me/', data=data, content_type='multipart/form-data', **headers)
print("RESPONSE STATUS:", response.status_code)
try:
    print("RESPONSE DATA:", response.json())
except:
    print("RESPONSE CONTENT:", response.content)

# Check what GET returns
get_response = client.get('/api/account/me/', **headers)
print("GET STATUS:", get_response.status_code)
print("GET DATA:", get_response.json())

# Check what the user model has
user.refresh_from_db()
print("DB USER FIRST NAME:", user.first_name)
print("DB USER LAST NAME:", user.last_name)

user.delete()
