# events/serializers/event_setup.py
from django.utils import timezone
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from ..models import Event, CustomQuestion
from tickets.models import TicketType
from .vendor_invite import VendorInviteSerializer

class NestedTicketTypeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = TicketType
        fields = ("id", "name", "description", "price", "quantity")

class NestedCustomQuestionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)

    class Meta:
        model = CustomQuestion
        fields = ("id", "question_text", "question_type", "options", "is_required", "order")

class EventListSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source="owner.username")
    registered_count = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "id", "title", "slug", "banner_image", "banner_portrait", "banner_video", "venue_name", "start_date", "end_date", "status", "owner_name", "registered_count", "currency", "country", "state_or_county", "registration_start", "registration_deadline", "attendees_notified_at"
        )

    @extend_schema_field(serializers.IntegerField())
    def get_registered_count(self, obj):
        return obj.registrations.count()

class EventDetailSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source="owner.first_name")
    is_live = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()
    ticket_types = NestedTicketTypeSerializer(many=True, read_only=True)
    custom_questions = NestedCustomQuestionSerializer(many=True, read_only=True)
    registered_count = serializers.SerializerMethodField()
    vendors = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            "id", "title", "slug", "description", "venue_name", "venue_address", "country", "state_or_county",
            "start_date", "end_date", "number_of_days", "registration_start", 
            "registration_deadline", "max_participants", "banner_image", "banner_portrait", "banner_video", 
            "status", "is_public", "is_public_gallery_enabled", "is_live", "can_register", "owner", "owner_name", 
            "ticket_types", "custom_questions", "registered_count", "currency", "vendors", "attendees_notified_at", "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "owner", "created_at", "updated_at")

    @extend_schema_field(serializers.BooleanField())
    def get_is_live(self, obj):
        return obj.is_live

    @extend_schema_field(serializers.BooleanField())
    def get_can_register(self, obj):
        return obj.can_register

    @extend_schema_field(serializers.IntegerField())
    def get_registered_count(self, obj):
        return obj.registrations.count()

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_vendors(self, obj):
        from .vendor_invite import EventVendorDetailSerializer
        return EventVendorDetailSerializer(obj.vendors.all(), many=True).data


class HybridImageField(serializers.ImageField):
    """
    Accepts either a real uploaded file, or a string that's already the final
    URL/path of a file uploaded directly to storage (S3/Cloudinary) via the
    presigned-upload flow — stored as-is so `.url` returns exactly that.
    """
    def to_internal_value(self, data):
        if isinstance(data, str):
            return data
        return super().to_internal_value(data)

class HybridFileField(serializers.FileField):
    """See HybridImageField — same passthrough behavior for string values."""
    def to_internal_value(self, data):
        if isinstance(data, str):
            return data
        return super().to_internal_value(data)

class EventCreateSerializer(serializers.ModelSerializer):
    ticket_types = NestedTicketTypeSerializer(many=True, required=False)
    custom_questions = NestedCustomQuestionSerializer(many=True, required=False)
    vendors = serializers.ListField(child=serializers.DictField(), required=False, write_only=True)
    
    banner_image = HybridImageField(required=False, allow_null=True)
    banner_portrait = HybridImageField(required=False, allow_null=True)
    banner_video = HybridFileField(required=False, allow_null=True)
    
    class Meta:
        model = Event
        exclude = ("slug", "owner")

    def to_internal_value(self, data):
        import json
        data_dict = {}
        if hasattr(data, "keys"):
            for k in data.keys():
                data_dict[k] = data.get(k)
        else:
            data_dict = dict(data)

        if "ticket_types" in data_dict and isinstance(data_dict["ticket_types"], str):
            try:
                data_dict["ticket_types"] = json.loads(data_dict["ticket_types"])
            except Exception:
                pass
                
        if "vendors" in data_dict and isinstance(data_dict["vendors"], str):
            try:
                data_dict["vendors"] = json.loads(data_dict["vendors"])
            except Exception:
                pass

        if "custom_questions" in data_dict and isinstance(data_dict["custom_questions"], str):
            try:
                data_dict["custom_questions"] = json.loads(data_dict["custom_questions"])
            except Exception:
                pass

        return super().to_internal_value(data_dict)

    def validate(self, attrs):
        is_partial = self.partial  # True for PATCH
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        registration_deadline = attrs.get("registration_deadline")
        registration_start = attrs.get("registration_start")

        now = timezone.now()

        if not is_partial:
            if start_date and start_date <= now:
                raise serializers.ValidationError({
                    "start_date": "Event start date must be in the future."
                })

            if registration_deadline and registration_deadline <= now:
                raise serializers.ValidationError({
                    "registration_deadline": "Registration deadline must be in the future."
                })

        if registration_start and start_date and registration_start >= start_date:
            raise serializers.ValidationError({
                "registration_start": "Registration must start before the event starts."
            })

        ticket_types = attrs.get("ticket_types", [])
        max_participants = attrs.get("max_participants", 100)
        total_capacity = sum(ticket.get("quantity", 0) for ticket in ticket_types)
        if ticket_types and total_capacity > max_participants:
            raise serializers.ValidationError({
                "ticket_types": f"The total ticket capacity across all categories ({total_capacity}) cannot exceed the event's max capacity ({max_participants})."
            })

        return attrs

    def create(self, validated_data):
        ticket_types_data = validated_data.pop("ticket_types", [])
        custom_questions_data = validated_data.pop("custom_questions", [])
        vendors_data = validated_data.pop("vendors", [])
        validated_data["owner"] = self.context["request"].user
        
        start_date = validated_data.get("start_date")
        end_date = validated_data.get("end_date")
        if start_date and end_date and "number_of_days" not in validated_data:
            delta = end_date - start_date
            validated_data["number_of_days"] = max(delta.days, 1)

        event = Event.objects.create(**validated_data)
        
        for ticket_data in ticket_types_data:
            ticket_data.pop("id", None)
            TicketType.objects.create(event=event, **ticket_data)

        for q_data in custom_questions_data:
            q_data.pop("id", None)
            CustomQuestion.objects.create(event=event, **q_data)
            
        for vendor_data in vendors_data:
            vendor_serializer = VendorInviteSerializer(
                data=vendor_data,
                context={"request": self.context.get("request"), "event": event}
            )
            if vendor_serializer.is_valid():
                vendor_serializer.save()
            
        return event

    def update(self, instance, validated_data):
        ticket_types_data = validated_data.pop("ticket_types", [])
        custom_questions_data = validated_data.pop("custom_questions", [])
        vendors_data = validated_data.pop("vendors", [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        keep_ids = []
        for ticket_data in ticket_types_data:
            ticket_id = ticket_data.get("id")
            if ticket_id:
                TicketType.objects.filter(id=ticket_id, event=instance).update(**{k: v for k, v in ticket_data.items() if k != 'id'})
                keep_ids.append(ticket_id)
            else:
                new_tt = TicketType.objects.create(event=instance, **{k: v for k, v in ticket_data.items() if k != 'id'})
                keep_ids.append(new_tt.id)
        TicketType.objects.filter(event=instance).exclude(id__in=keep_ids).delete()

        keep_q_ids = []
        for q_data in custom_questions_data:
            q_id = q_data.get("id")
            if q_id:
                CustomQuestion.objects.filter(id=q_id, event=instance).update(**{k: v for k, v in q_data.items() if k != 'id'})
                keep_q_ids.append(q_id)
            else:
                new_q = CustomQuestion.objects.create(event=instance, **{k: v for k, v in q_data.items() if k != 'id'})
                keep_q_ids.append(new_q.id)
        CustomQuestion.objects.filter(event=instance).exclude(id__in=keep_q_ids).delete()
                
        for vendor_data in vendors_data:
            vendor_serializer = VendorInviteSerializer(
                data=vendor_data,
                context={"request": self.context.get("request"), "event": instance}
            )
            if vendor_serializer.is_valid():
                vendor_serializer.save()
                
        return instance

