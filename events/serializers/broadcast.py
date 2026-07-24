from rest_framework import serializers
from ..models import BroadcastMessage

class BroadcastMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BroadcastMessage
        fields = ("id", "event", "subject", "message", "recipient_type", "channel", "sent_at", "sent_count")
        read_only_fields = ("id", "event", "sent_at", "sent_count")
