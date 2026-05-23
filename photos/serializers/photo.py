from rest_framework import serializers
from ..models import EventPhoto


class EventPhotoSerializer(serializers.ModelSerializer):

    uploaded_by_username = serializers.ReadOnlyField(
        source="uploaded_by.username"
    )

    class Meta:

        model = EventPhoto

        fields = (
            "id",
            "event",
            "uploaded_by",
            "uploaded_by_username",
            "image",
            "caption",
            "is_processed",
            "created_at",
        )

        read_only_fields = (
            "id",
            "uploaded_by",
            "is_processed",
            "created_at",
        )
