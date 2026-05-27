# tickets/serializers/attendee_dashboard.py
from rest_framework import serializers
from ..models import EventRegistration
from accounts.models import AttendeeProfile


class AttendeeUpcomingEventSerializer(serializers.ModelSerializer):
    event_id = serializers.UUIDField(source="event.id", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)
    event_slug = serializers.CharField(source="event.slug", read_only=True)
    event_banner = serializers.ImageField(
        source="event.banner_image",
        read_only=True,
    )
    venue_name = serializers.CharField(
        source="event.venue_name",
        read_only=True,
    )
    venue_address = serializers.CharField(
        source="event.venue_address",
        read_only=True,
    )
    start_date = serializers.DateTimeField(
        source="event.start_date",
        read_only=True,
    )
    end_date = serializers.DateTimeField(
        source="event.end_date",
        read_only=True,
    )
    ticket_type_name = serializers.CharField(
        source="ticket_type.name",
        read_only=True,
    )
    ticket_price = serializers.DecimalField(
        source="ticket_type.price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    qr_available = serializers.SerializerMethodField()
    number_of_days = serializers.IntegerField(source="event.number_of_days", read_only=True)
    event_location = serializers.SerializerMethodField()
    is_event_active = serializers.SerializerMethodField()
    event_start_date = serializers.DateTimeField(source="event.start_date", read_only=True)
    event_end_date = serializers.DateTimeField(source="event.end_date", read_only=True)

    class Meta:
        model = EventRegistration
        fields = ("id", "registration_code", "status", "checked_in", "registered_at",
            "event_id", "event_title", "event_slug", "event_banner", "venue_name", "venue_address",
            "start_date", "end_date", "event_start_date", "event_end_date",
            "ticket_type_name", "ticket_price",
            "qr_code", "qr_available",
            "number_of_days", "event_location", "is_event_active",
        )

    def get_qr_available(self, obj):
        return bool(obj.qr_code)

    def get_event_location(self, obj):
        parts = [obj.event.venue_name, obj.event.venue_address]
        return ', '.join(p for p in parts if p) or ''

    def get_is_event_active(self, obj):
        from django.utils import timezone
        now = timezone.now()
        return obj.event.start_date <= now <= obj.event.end_date if obj.event.start_date and obj.event.end_date else False
    

class AttendeeEventHistorySerializer(serializers.ModelSerializer):

    # ------------------------------------------
    # Event fields
    # ------------------------------------------

    event_id = serializers.UUIDField(
        source="event.id",
        read_only=True,
    )

    event_title = serializers.CharField(
        source="event.title",
        read_only=True,
    )

    event_slug = serializers.CharField(
        source="event.slug",
        read_only=True,
    )

    event_banner = serializers.ImageField(
        source="event.banner_image",
        read_only=True,
    )

    venue_name = serializers.CharField(
        source="event.venue_name",
        read_only=True,
    )

    start_date = serializers.DateTimeField(
        source="event.start_date",
        read_only=True,
    )

    end_date = serializers.DateTimeField(
        source="event.end_date",
        read_only=True,
    )

    event_status = serializers.CharField(
        source="event.status",
        read_only=True,
    )

    # ------------------------------------------
    # Ticket fields
    # ------------------------------------------

    ticket_type_name = serializers.CharField(
        source="ticket_type.name",
        read_only=True,
    )

    ticket_price = serializers.DecimalField(
        source="ticket_type.price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    # ------------------------------------------
    # Attendance fields
    # ------------------------------------------

    attended_at = serializers.SerializerMethodField()
    qr_available = serializers.SerializerMethodField()
    number_of_days = serializers.IntegerField(source="event.number_of_days", read_only=True)
    event_location = serializers.SerializerMethodField()
    is_event_active = serializers.SerializerMethodField()
    event_start_date = serializers.DateTimeField(source="event.start_date", read_only=True)
    event_end_date = serializers.DateTimeField(source="event.end_date", read_only=True)

    class Meta:
        model = EventRegistration
        fields = (
            "id", "registration_code",
            "status", "checked_in", "registered_at", "attended_at",
            "event_id", "event_title", "event_slug", "event_banner", "venue_name", "start_date", "end_date",
            "event_start_date", "event_end_date", "event_status",
            "ticket_type_name", "ticket_price",
            "qr_code", "qr_available",
            "number_of_days", "event_location", "is_event_active",
        )

    def get_attended_at(self, obj):
        if obj.checked_in:
            return obj.registered_at
        return None

    def get_qr_available(self, obj):
        return bool(obj.qr_code)

    def get_event_location(self, obj):
        parts = [obj.event.venue_name, obj.event.venue_address]
        return ', '.join(p for p in parts if p) or ''

    def get_is_event_active(self, obj):
        from django.utils import timezone
        now = timezone.now()
        return obj.event.start_date <= now <= obj.event.end_date if obj.event.start_date and obj.event.end_date else False


class AttendeeRegistrationDetailSerializer(serializers.ModelSerializer):

    # ------------------------------------------
    # Event Info
    # ------------------------------------------

    event_id = serializers.UUIDField(
        source="event.id",
        read_only=True,
    )

    event_title = serializers.CharField(
        source="event.title",
        read_only=True,
    )

    event_slug = serializers.CharField(
        source="event.slug",
        read_only=True,
    )

    event_description = serializers.CharField(
        source="event.description",
        read_only=True,
    )

    venue_name = serializers.CharField(
        source="event.venue_name",
        read_only=True,
    )

    venue_address = serializers.CharField(
        source="event.venue_address",
        read_only=True,
    )

    start_date = serializers.DateTimeField(
        source="event.start_date",
        read_only=True,
    )

    end_date = serializers.DateTimeField(
        source="event.end_date",
        read_only=True,
    )

    banner_image = serializers.ImageField(source="event.banner_image", read_only=True,)
    
    event_currency = serializers.CharField(source="event.currency", read_only=True)

    # ------------------------------------------
    # Ticket Info
    # ------------------------------------------

    ticket_type_name = serializers.CharField(
        source="ticket_type.name",
        read_only=True,
    )

    ticket_price = serializers.DecimalField(
        source="ticket_type.price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    # ------------------------------------------
    # Attendee Info
    # ------------------------------------------

    attendee_name = serializers.CharField(source="attendee.full_name", read_only=True)
    attendee_email = serializers.EmailField(source="attendee.email", read_only=True)
    checkin_history = serializers.SerializerMethodField()
    attendance_days_count = serializers.SerializerMethodField()
    number_of_days = serializers.IntegerField(source="event.number_of_days", read_only=True)
    event_start_date_raw = serializers.DateTimeField(source="event.start_date", read_only=True)

    class Meta:
        model = EventRegistration
        fields = (
            "id", "registration_code", "status", "checked_in", "registered_at",
            "event_id", "event_title", "event_slug", "event_description",
            "venue_name", "venue_address", "start_date", "end_date", "banner_image", "event_currency",
            "ticket_type_name", "ticket_price",
            "qr_code",
            "attendee_name", "attendee_email",
            "checkin_history", "attendance_days_count", "number_of_days", "event_start_date_raw",
        )

    def get_checkin_history(self, obj):
        return [
            {
                "date": str(c.date),
                "time": str(c.time),
                "device_id": c.device_id or "Unknown Device",
            }
            for c in obj.daily_checkins.all()
        ]

    def get_attendance_days_count(self, obj):
        return obj.daily_checkins.count()


class AttendeeProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = AttendeeProfile
        fields = [
            "id",
            "full_name",
            "email",
            "phone_number",
            # "date_of_birth",
            # "gender",
            # "profile_picture",
            # "bio",
            # "is_facial_recognition_enabled",   # for future facial recognition
            # "marketing_consent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email", "created_at", "updated_at"]


class AttendeeActiveTicketSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for gate entry / ticket scanning.
    Lightweight and focused on quick verification.
    """

    # Event Information
    event_id = serializers.UUIDField(source="event.id", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)
    event_slug = serializers.CharField(source="event.slug", read_only=True)
    event_banner = serializers.ImageField(source="event.banner_image", read_only=True)

    venue_name = serializers.CharField(source="event.venue_name", read_only=True)
    venue_address = serializers.CharField(source="event.venue_address", read_only=True)

    start_date = serializers.DateTimeField(source="event.start_date", read_only=True)
    end_date = serializers.DateTimeField(source="event.end_date", read_only=True)

    # Ticket Information
    ticket_type_name = serializers.CharField(source="ticket_type.name", read_only=True)
    ticket_price = serializers.DecimalField(
        source="ticket_type.price", 
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )

    # Attendee Info
    attendee_name = serializers.CharField(
        source="attendee.full_name", 
        read_only=True
    )
    attendee_email = serializers.EmailField(
        source="attendee.email", 
        read_only=True
    )

    # QR Code & Status
    qr_available = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = EventRegistration
        fields = [
            # Core Identification
            "id",
            "registration_code",           # Important for manual lookup

            # Attendee
            "attendee_name",
            "attendee_email",

            # Event
            "event_id",
            "event_title",
            "event_slug",
            "event_banner",
            "venue_name",
            "venue_address",
            "start_date",
            "end_date",

            # Ticket
            "ticket_type_name",
            "ticket_price",

            # Status & QR
            "status",
            "checked_in",
            "registered_at",
            "qr_code",
            "qr_available",
            "is_valid",
        ]

    def get_qr_available(self, obj):
        """Check if QR code exists"""
        return bool(obj.qr_code)

    def get_is_valid(self, obj):
        """
        Determines if ticket is valid for entry.
        You can enhance this logic later (e.g., check date, blacklist, etc.)
        """
        return (
            obj.status == EventRegistration.Status.CONFIRMED
            and not obj.checked_in
        )