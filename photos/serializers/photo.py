from rest_framework import serializers
from ..models import Photo


class PhotoSerializer(serializers.ModelSerializer):

    uploader_username = serializers.ReadOnlyField(
        source="uploader.username"
    )

    class Meta:
        model = Photo
        fields = (
            "id",
            "event",
            "uploader",
            "uploader_username",
            "media_file",
            "thumbnail_url",
            "caption",
            "ai_status",
            "is_public",
            "created_at",
        )

        read_only_fields = (
            "id",
            "uploader",
            "ai_status",
            "created_at",
        )
