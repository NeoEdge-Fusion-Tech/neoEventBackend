# tickets/serializers/event_ticketing.py
import uuid
from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from ..models import TicketType, EventRegistration
from accounts.models import AttendeeProfile
from accounts.tasks import process_biometric_image
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
    full_name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    phone_number = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    group_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    attendees = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True
    )
    reference_image = serializers.ImageField(required=False, write_only=True)
    ai_consent = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = EventRegistration
        fields = (
            "id", "event", "ticket_type", "full_name", "email", "phone_number", 
            "group_name", "attendees", "registration_code", "status", "registered_at",
            "reference_image", "ai_consent",
        )
        read_only_fields = (
            "registration_code", "status", "registered_at",
        )

    def to_internal_value(self, data):
        import json
        data_dict = {}
        if hasattr(data, "keys"):
            for k in data.keys():
                data_dict[k] = data.get(k)
        else:
            data_dict = dict(data)

        if "attendees" in data_dict and isinstance(data_dict["attendees"], str):
            try:
                data_dict["attendees"] = json.loads(data_dict["attendees"])
            except Exception:
                pass
        return super().to_internal_value(data_dict)

    def validate(self, attrs):
        event = attrs["event"]
        ticket_type = attrs["ticket_type"]
        attendees = self.initial_data.get("attendees")

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
        # Enforce Mandatory Email & Phone and Prevent Duplicates
        # ---------------------------------------------------
        if not attendees:
            email = self.initial_data.get("email")
            phone = self.initial_data.get("phone_number")
            
            if not email:
                raise serializers.ValidationError({"email": "Email is required for ticket purchase."})
            if not phone:
                raise serializers.ValidationError({"phone_number": "Phone number is required for ticket purchase."})
            
            existing_attendee = AttendeeProfile.objects.filter(email=email).first()
            if existing_attendee:
                already_registered = EventRegistration.objects.filter(
                    event=event,
                    attendee=existing_attendee,
                ).exists()
                if already_registered:
                    raise serializers.ValidationError({
                        "email": "This attendee is already registered for this event."
                    })
        else:
            for att in attendees:
                if not att.get("email"):
                    raise serializers.ValidationError({"attendees": "Email is required for all group members."})
                if not att.get("phone_number") and not att.get("phone"):
                    raise serializers.ValidationError({"attendees": "Phone number is required for all group members."})

        return attrs

    def create(self, validated_data):
        attendees = validated_data.pop("attendees", None)
        group_name = validated_data.get("group_name", None)
        event = validated_data["event"]
        ticket_type_val = validated_data["ticket_type"]

        with transaction.atomic():
            # ---------------------------------------------------
            # Lock ticket row
            # ---------------------------------------------------
            ticket_type = (
                TicketType.objects
                .select_for_update()
                .get(id=ticket_type_val.id)
            )

            quantity = len(attendees) if attendees else 1
            remaining = ticket_type.quantity - ticket_type.sold_count

            if remaining < quantity:
                raise serializers.ValidationError({
                    "ticket_type": f"Tickets are sold out. Only {remaining} remaining."
                })

            group_code = uuid.uuid4() if (attendees and len(attendees) > 1) or group_name else None
            
            # Determine status based on ticket price
            registration_status = EventRegistration.Status.CONFIRMED
            if ticket_type.price > 0:
                registration_status = EventRegistration.Status.PENDING

            if attendees:
                registrations = []
                for idx, att in enumerate(attendees):
                    name = att.get("full_name") or att.get("name")
                    email = att.get("email")
                    phone = att.get("phone_number") or att.get("phone", "")

                    attendee, _ = AttendeeProfile.objects.get_or_create(
                        email=email,
                        defaults={
                            "full_name": name,
                            "phone_number": phone,
                        }
                    )
                    
                    # Ensure User exists and is linked
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    
                    parts = name.split(' ') if name else []
                    first_name = parts[0] if len(parts) > 0 else ''
                    last_name = parts[1] if len(parts) > 1 else ''
                    
                    user, user_created = User.objects.get_or_create(email=email, defaults={
                        'username': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone_number': phone,
                        'role': 'ATTENDEE',
                        'is_active': True
                    })
                    if user_created:
                        user.set_unusable_password()
                        user.save()
                    
                    if not attendee.user_id:
                        attendee.user = user
                        attendee.save()
                    
                    ref_img = self.initial_data.get(f"reference_image_{idx}")
                    if ref_img and getattr(ref_img, "size", None):
                        attendee.reference_image = ref_img
                        attendee.save()
                        # Trigger the AI embedding task asynchronously
                        process_biometric_image.delay(attendee.email, attendee.reference_image.url, user_id=str(user.id))

                    reg = EventRegistration.objects.create(
                        event=event,
                        ticket_type=ticket_type,
                        attendee=attendee,
                        attendee_name=name,
                        attendee_email=email,
                        group_name=group_name,
                        group_code=group_code,
                        status=registration_status,
                        ai_consent=validated_data.get("ai_consent", False),
                    )
                    registrations.append(reg)

                # Atomic increment
                TicketType.objects.filter(id=ticket_type.id).update(
                    sold_count=F("sold_count") + quantity
                )
                return registrations[0]
            else:
                full_name = validated_data.pop("full_name")
                email = validated_data.pop("email")
                phone_number = validated_data.pop("phone_number", "")
                reference_image = validated_data.pop("reference_image", None)

                attendee, _ = AttendeeProfile.objects.get_or_create(
                    email=email,
                    defaults={
                        "full_name": full_name,
                        "phone_number": phone_number,
                    }
                )
                if reference_image:
                    attendee.reference_image = reference_image
                    attendee.save()
                    # Trigger the AI embedding task asynchronously
                    process_biometric_image.delay(attendee.email, attendee.reference_image.url)

                registration = EventRegistration.objects.create(
                    attendee=attendee,
                    attendee_name=full_name,
                    attendee_email=email,
                    group_name=group_name,
                    group_code=group_code,
                    status=registration_status,
                    **validated_data
                )

                TicketType.objects.filter(id=ticket_type.id).update(
                    sold_count=F("sold_count") + 1
                )
                return registration

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add requires_payment flag for the frontend
        representation["requires_payment"] = instance.ticket_type and instance.ticket_type.price > 0
        return representation

class EventRegistrationListSerializer(serializers.ModelSerializer):
    attendee_name_display = serializers.SerializerMethodField()
    attendee_email_display = serializers.SerializerMethodField()
    ticket_type_name = serializers.ReadOnlyField(source="ticket_type.name")
    ticket_type_price = serializers.ReadOnlyField(source="ticket_type.price")
    attendance_days_count = serializers.SerializerMethodField()
    checkin_history = serializers.SerializerMethodField()

    class Meta:
        model = EventRegistration
        fields = (
            "id", "attendee_name_display", "attendee_email_display", "group_name", "group_code",
            "ticket_type_name", "ticket_type_price", "registration_code", "checked_in", "status", "registered_at",
            "attendance_days_count", "checkin_history",
        )

    @extend_schema_field(serializers.CharField())
    def get_attendee_name_display(self, obj):
        if obj.attendee_name:
            return obj.attendee_name
        return obj.attendee.full_name if obj.attendee else "Unknown"

    @extend_schema_field(serializers.CharField())
    def get_attendee_email_display(self, obj):
        if obj.attendee_email:
            return obj.attendee_email
        return obj.attendee.email if obj.attendee else ""

    @extend_schema_field(serializers.IntegerField())
    def get_attendance_days_count(self, obj):
        return obj.daily_checkins.count()

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_checkin_history(self, obj):
        return [
            {
                "date": str(c.date),
                "time": str(c.time),
                "device_id": c.device_id
            }
            for c in obj.daily_checkins.all()
        ]