from rest_framework import serializers
from .models import TicketType, EventRegistration
from accounts.models import AttendeeProfile
from django.db import transaction
from drf_spectacular.utils import extend_schema_field


class TicketTypeSerializer(serializers.ModelSerializer):
    remaining = serializers.ReadOnlyField()

    class Meta:
        model = TicketType
        fields = (
            "id", "name", "description", "price", 
            "quantity", "sold_count", "remaining", "is_active",
        )

    @extend_schema_field(serializers.IntegerField())
    def get_remaining(self, obj):
        return obj.remaining


class EventRegistrationSerializer(serializers.ModelSerializer):
    # These extra fields MUST be in the 'fields' tuple below
    full_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = EventRegistration
        fields = (
            "id",
            "event",
            "ticket_type",
            "full_name",   
            "email",       
            "phone_number",
            "registration_code",
            "status",
            "registered_at",
        )
        read_only_fields = (
            "registration_code",
            "status",
            "registered_at",
        )

    def validate(self, attrs):
        ticket_type = attrs.get("ticket_type")
        if ticket_type and ticket_type.remaining <= 0:
            raise serializers.ValidationError({
                "ticket_type": "Tickets for this category are sold out."
            })
        return attrs

    def create(self, validated_data):
        # 1. Extract the write-only fields
        full_name = validated_data.pop("full_name")
        email = validated_data.pop("email")
        phone_number = validated_data.pop("phone_number", "")

        # Use an atomic transaction to ensure data integrity
        with transaction.atomic():
            # 2. Get or create the attendee profile
            attendee, _ = AttendeeProfile.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": full_name,
                    "phone_number": phone_number,
                }
            )

            # 3. Create the registration
            # We pass the found attendee into the model creation
            registration = EventRegistration.objects.create(
                attendee=attendee,
                **validated_data
            )

            # 4. Update the ticket inventory
            ticket_type = validated_data["ticket_type"]
            ticket_type.sold_count += 1
            ticket_type.save()

            return registration
        
