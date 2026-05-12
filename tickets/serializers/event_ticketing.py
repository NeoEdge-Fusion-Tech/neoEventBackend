# tickets/serializers/event_ticketing.py
from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from ..models import TicketType, EventRegistration
from accounts.models import AttendeeProfile
from drf_spectacular.utils import extend_schema_field


class TicketTypeSerializer(serializers.ModelSerializer):
    remaining = serializers.ReadOnlyField()

    class Meta:
        model = TicketType
        fields = (
            "id", "name", "description", "price", "quantity", "sold_count", "remaining", "is_active",
        )

    @extend_schema_field(serializers.IntegerField())
    def get_remaining(self, obj):
        return obj.remaining


class EventRegistrationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone_number = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = EventRegistration

        fields = (
            "id", "event", "ticket_type", "full_name", "email", "phone_number", "registration_code", "status", "registered_at",
        )

        read_only_fields = (
            "registration_code", "status", "registered_at",
        )

    def validate(self, attrs):

        event = attrs["event"]
        ticket_type = attrs["ticket_type"]

        email = self.initial_data.get("email")

        # ---------------------------------------------------
        # Ensure event is open for registration
        # ---------------------------------------------------
        if not event.can_register:
            raise serializers.ValidationError({
                "event": "Registration is closed for this event."
            })

        # ---------------------------------------------------
        # Ensure ticket belongs to this event
        # ---------------------------------------------------

        if ticket_type.event_id != event.id:
            raise serializers.ValidationError({
                "ticket_type": "This ticket does not belong to the selected event."
            })

        # ---------------------------------------------------
        # Ensure ticket is active
        # ---------------------------------------------------

        if not ticket_type.is_active:
            raise serializers.ValidationError({
                "ticket_type": "This ticket type is not active."
            })

        # ---------------------------------------------------
        # Prevent duplicate registration
        # ---------------------------------------------------

        existing_attendee = AttendeeProfile.objects.filter(
            email=email
        ).first()

        if existing_attendee:

            already_registered = EventRegistration.objects.filter(
                event=event,
                attendee=existing_attendee,
            ).exists()

            if already_registered:
                raise serializers.ValidationError({
                    "email": "This attendee is already registered for this event."
                })

        return attrs

    def create(self, validated_data):

        full_name = validated_data.pop("full_name")
        email = validated_data.pop("email")
        phone_number = validated_data.pop("phone_number", "")

        with transaction.atomic():

            # ---------------------------------------------------
            # Lock ticket row
            # ---------------------------------------------------

            ticket_type = (
                TicketType.objects
                .select_for_update()
                .get(id=validated_data["ticket_type"].id)
            )

            # ---------------------------------------------------
            # Re-check inventory inside lock
            # ---------------------------------------------------

            remaining = ticket_type.quantity - ticket_type.sold_count

            if remaining <= 0:
                raise serializers.ValidationError({
                    "ticket_type": "Tickets are sold out."
                })

            # ---------------------------------------------------
            # Get/Create attendee
            # ---------------------------------------------------

            attendee, _ = AttendeeProfile.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": full_name,
                    "phone_number": phone_number,
                }
            )

            # ---------------------------------------------------
            # Create registration
            # ---------------------------------------------------

            registration = EventRegistration.objects.create(
                attendee=attendee,
                ticket_type=ticket_type,
                **validated_data
            )

            # ---------------------------------------------------
            # Atomic inventory increment
            # ---------------------------------------------------

            TicketType.objects.filter(
                id=ticket_type.id
            ).update(
                sold_count=F("sold_count") + 1
            )

            return registration
        