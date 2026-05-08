# events/serializers/event_setup.py
from django.utils import timezone
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from ..models import Event

class EventListSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Event
        fields = (
            "id", "title", "slug", "banner_image",  "venue_name", "start_date", "status", "owner_name",
        )

class EventDetailSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source="owner.username")
    # Explicitly telling Swagger these are Boolean fields
    is_live = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "id", "title", "slug", "description", "venue_name",  "venue_address", "start_date", "end_date",  "registration_deadline", "banner_image", "status", "is_public", "is_live", "can_register", "owner",  "owner_name", "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "owner", "created_at", "updated_at")

    @extend_schema_field(serializers.BooleanField())
    def get_is_live(self, obj):
        return obj.is_live

    @extend_schema_field(serializers.BooleanField())
    def get_can_register(self, obj):
        return obj.can_register

class EventCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Event
        exclude = ("id", "slug", "owner", "created_at", "updated_at")

    def validate(self, attrs):
        # Your existing date validation logic is perfect here
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        registration_deadline = attrs.get("registration_deadline")

        now = timezone.now()

        if start_date <= now:
            raise serializers.ValidationError({
                "start_date": "Event start date must be in the future."
            })

        if registration_deadline <= now:
            raise serializers.ValidationError({
                "registration_deadline": "Registration deadline must be in the future."
            })

        # if end_date <= start_date:
        #     raise serializers.ValidationError({"end_date": "End date must be after start date."})

        # if registration_deadline > start_date:
        #     raise serializers.ValidationError({
        #         "registration_deadline": "Registration deadline must be before event start date."
        #     })
        return attrs

    def create(self, validated_data):
        # Good use of context! This ensures the owner is the logged-in user.
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)

