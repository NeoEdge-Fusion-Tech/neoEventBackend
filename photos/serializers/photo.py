from rest_framework import serializers
from ..models import Photo


class PhotoSerializer(serializers.ModelSerializer):

    uploader_username = serializers.ReadOnlyField(source="uploader.username")
    uploader_full_name = serializers.SerializerMethodField()
    uploader_email = serializers.ReadOnlyField(source="uploader.email")
    media_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = (
            "id",
            "event",
            "uploader",
            "uploader_username",
            "uploader_full_name",
            "uploader_email",
            "media_file",
            "media_file_url",
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

    def get_uploader_full_name(self, obj):
        u = obj.uploader
        name = f"{u.first_name} {u.last_name}".strip()
        return name or u.username

    def get_media_file_url(self, obj):
        request = self.context.get("request")
        if obj.media_file and request:
            try:
                return request.build_absolute_uri(obj.media_file.url)
            except Exception:
                pass
        if obj.media_file:
            return str(obj.media_file)
        return None
