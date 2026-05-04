
from rest_framework import serializers
from .models import Event

class EventListSerializer(serializers.ModelSerializer):

    owner_name = serializers.ReadOnlyField(
        source="owner.username"
    )

    class Meta:
        model = Event

        fields = (
            "id",
            "title",
            "slug",
            "banner_image",
            "venue_name",
            "start_date",
            "status",
            "owner_name",
        )


class EventDetailSerializer(serializers.ModelSerializer):

    owner_name = serializers.ReadOnlyField(
        source="owner.username"
    )

    is_live = serializers.ReadOnlyField()

    can_register = serializers.ReadOnlyField()

    class Meta:
        model = Event

        fields = (
            "id",
            "title",
            "slug",
            "description",
            "venue_name",
            "venue_address",
            "start_date",
            "end_date",
            "registration_deadline",
            "banner_image",
            "status",
            "is_public",
            "is_live",
            "can_register",
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "slug",
            "owner",
            "created_at",
            "updated_at",
        )


class EventCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Event

        exclude = (
            "id",
            "slug",
            "owner",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):

        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        registration_deadline = attrs.get("registration_deadline")

        if end_date <= start_date:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date."
            })

        if registration_deadline > start_date:
            raise serializers.ValidationError({
                "registration_deadline":
                "Registration deadline must be before event start date."
            })

        return attrs

    def create(self, validated_data):

        validated_data["owner"] = self.context["request"].user

        return super().create(validated_data)

        
# class EventDetailSerializer(serializers.ModelSerializer):

#     ticket_types = TicketTypeSerializer(many=True)

#     vendors = EventVendorSerializer(many=True)

#     class Meta:
#         model = Event
#         fields = "__all__"


# class EventPhotographerSerializer(serializers.ModelSerializer):
#     photographer_name = serializers.ReadOnlyField(source='photographer.username')
    
#     class Meta:
#         model = EventPhotographer
#         fields = ('id', 'event', 'photographer', 'photographer_name', 'email', 'unique_code', 'invitation_sent', 'created_at')
#         read_only_fields = ('unique_code', 'invitation_sent', 'created_at')

# class EventSerializer(serializers.ModelSerializer):
#     owner_name = serializers.ReadOnlyField(source='owner.username')
#     is_currently_holding = serializers.ReadOnlyField()
#     event_photographers = EventPhotographerSerializer(many=True, read_only=True)

#     class Meta:
#         model = Event
#         fields = (
#             'id', 'title', 'description', 'start_date', 'end_date', 'location', 
#             'registration_deadline', 'status', 'is_currently_holding', 'is_paid', 
#             'price', 'banner_image', 'owner', 'owner_name', 'event_photographers', 
#             'created_at'
#         )
#         read_only_fields = ('owner', 'owner_name', 'is_currently_holding', 'created_at')
