# events/serializers/vendor_invite.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import EventVendor 
from accounts.models import VendorProfile

User = get_user_model()

class VendorInviteSerializer(serializers.ModelSerializer):
    """
    Used by an event owner to invite a vendor.
    Accepts the vendor's email (or username) and role.
    The event is injected from the URL, not from the request body.
    """
    vendor_email = serializers.EmailField(write_only=True)

    class Meta:
        model = EventVendor
        fields = ("vendor_email", "role")

    def validate_vendor_email(self, value):

        try:
            user = User.objects.select_related(
                "vendor_profile"
            ).get(email=value)

        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No registered user found with this email address."
            )

        if user.role != User.Role.VENDOR:
            raise serializers.ValidationError(
                "This user is not registered as a vendor."
            )

        if not hasattr(user, "vendor_profile"):
            raise serializers.ValidationError(
                "Vendor profile is missing for this user."
            )

        return user

    def validate(self, attrs):

        event = self.context["event"]

        vendor = attrs["vendor_email"]

        if vendor == event.owner:
            raise serializers.ValidationError(
                "The event owner cannot be added as a vendor."
            )

        if EventVendor.objects.filter(
            event=event,
            vendor=vendor,
            role=attrs["role"]
        ).exists():
            raise serializers.ValidationError(
                f"This vendor already has the '{attrs['role']}' role on this event."
            )

        vendor_profile = vendor.vendor_profile

        role_mapping = {
            EventVendor.VendorRole.PHOTOGRAPHER:
                VendorProfile.VendorSubtype.PHOTOGRAPHER,

            EventVendor.VendorRole.VIDEOGRAPHER:
                VendorProfile.VendorSubtype.VIDEOGRAPHER,

            EventVendor.VendorRole.PLANNER:
                VendorProfile.VendorSubtype.PLANNER,
        }

        expected_subtype = role_mapping.get(attrs["role"])

        if vendor_profile.subtype != expected_subtype:
            raise serializers.ValidationError(
                f"This vendor is registered as "
                f"'{vendor_profile.get_subtype_display()}' "
                f"and cannot be assigned the role "
                f"'{attrs['role']}'."
            )

        return attrs

    def create(self, validated_data):
        event = self.context["event"]
        vendor = validated_data.pop("vendor_email")  # User object
        return EventVendor.objects.create(
            event=event,
            vendor=vendor,
            **validated_data
            # invitation_code auto-generated, is_confirmed=False by default
        )


class EventVendorDetailSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for displaying vendor details on an event.
    Used in list/retrieve responses.
    """
    vendor_username = serializers.ReadOnlyField(source="vendor.username")
    vendor_email = serializers.ReadOnlyField(source="vendor.email")
    role_display = serializers.ReadOnlyField(source="get_role_display")

    class Meta:
        model = EventVendor
        fields = (
            "id",
            "vendor",
            "vendor_username",
            "vendor_email",
            "role",
            "role_display",
            "is_confirmed",
            "invited_at",
        )
        read_only_fields = fields


class VendorAcceptInviteSerializer(serializers.Serializer):
    """
    Used by the invited vendor to accept or decline.
    Accepts a boolean `accept` field alongside the invitation_code from the URL.
    """
    accept = serializers.BooleanField(
        help_text="Set to true to accept the invitation, false to decline."
    )

