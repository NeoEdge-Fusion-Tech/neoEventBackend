# tickets/serializers/checkin.py

from rest_framework import serializers
from models import EventRegistration


class EventCheckInSerializer(serializers.ModelSerializer):

    attendee_name = serializers.ReadOnlyField(
        source="attendee.full_name"
    )

    event_title = serializers.ReadOnlyField(
        source="event.title"
    )

    class Meta:

        model = EventRegistration

        fields = (
            "registration_code",
            "attendee_name",
            "event_title",
            "status",
            "checked_in",
            "registered_at",
        )
