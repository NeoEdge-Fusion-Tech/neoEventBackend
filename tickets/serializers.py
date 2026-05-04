
# # tickets/serializers.py
from rest_framework import serializers

from .models import (
    TicketType,
    EventRegistration,
)

from accounts.models import AttendeeProfile

class TicketTypeSerializer(serializers.ModelSerializer):

    remaining = serializers.ReadOnlyField()

    class Meta:
        model = TicketType

        fields = (
            "id",
            "name",
            "description",
            "price",
            "quantity",
            "sold_count",
            "remaining",
            "is_active",
        )


class EventRegistrationSerializer(serializers.ModelSerializer):

    full_name = serializers.CharField(write_only=True)

    email = serializers.EmailField(write_only=True)

    phone_number = serializers.CharField(
        write_only=True,
        required=False
    )

    class Meta:
        model = EventRegistration

        fields = (
            "id",
            "event",
            "ticket_type",
            "full_name",
            "email",
            "phone_number",
            "image_permission",
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

        if ticket_type.remaining <= 0:
            raise serializers.ValidationError({
                "ticket_type": "Tickets sold out."
            })

        return attrs

    def create(self, validated_data):

        full_name = validated_data.pop("full_name")

        email = validated_data.pop("email")

        phone_number = validated_data.pop(
            "phone_number",
            ""
        )

        attendee, _ = AttendeeProfile.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name,
                "phone_number": phone_number,
            }
        )

        ticket_type = validated_data["ticket_type"]

        registration = EventRegistration.objects.create(
            attendee=attendee,
            **validated_data
        )

        ticket_type.sold_count += 1
        ticket_type.save()

        return registration

# from rest_framework import serializers
# from .models import Registration, Ticket

# class TicketSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Ticket
#         fields = ('id', 'ticket_id', 'qr_code')

# class RegistrationSerializer(serializers.ModelSerializer):
#     ticket = TicketSerializer(read_only=True)
#     event_title = serializers.ReadOnlyField(source='event.title')
#     event_start_date = serializers.ReadOnlyField(source='event.start_date')
#     event_end_date = serializers.ReadOnlyField(source='event.end_date')
#     event_location = serializers.ReadOnlyField(source='event.location')
#     event_banner = serializers.ImageField(source='event.banner_image', read_only=True)
#     is_event_active = serializers.ReadOnlyField(source='event.is_currently_holding')

#     class Meta:
#         model = Registration
#         fields = (
#             'id', 'user', 'event', 'event_title', 'event_start_date', 
#             'event_end_date', 'event_location', 'event_banner', 
#             'is_event_active', 'registered_at', 'image_permission', 
#             'is_paid', 'payment_reference', 'ticket'
#         )
#         read_only_fields = ('user', 'registered_at', 'ticket')

