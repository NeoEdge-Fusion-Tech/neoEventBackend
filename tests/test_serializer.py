import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from accounts.models import User
from tickets.models import EventRegistration
from tickets.serializers.attendee_dashboard import AttendeeEventHistorySerializer

user = User.objects.get(email='sunnex0.ajayi@gmail.com')
qs = EventRegistration.objects.filter(attendee_email=user.email).exclude(status='CANCELLED')

serializer = AttendeeEventHistorySerializer(qs, many=True)
try:
    print(serializer.data)
except Exception as e:
    import traceback
    traceback.print_exc()

