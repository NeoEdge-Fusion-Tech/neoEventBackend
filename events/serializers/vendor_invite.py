# events/serializers/vendor_invite.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import EventVendor 
from accounts.models import VendorProfile

User = get_user_model()

class VendorInviteSerializer(serializers.ModelSerializer):
    """
    Used by an event owner to invite a vendor.
    Accepts the vendor's email and role.
    The event is injected from the URL, not from the request body.
    """
    vendor_email = serializers.EmailField(write_only=True)
    vendor_name = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    vendor_phone = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = EventVendor
        fields = ("vendor_email", "vendor_name", "vendor_phone", "role")

    def validate(self, attrs):
        event = self.context["event"]
        email = attrs["vendor_email"]
        role = attrs["role"].upper()
        attrs["role"] = role

        if event.owner.email == email:
            raise serializers.ValidationError(
                "The event owner cannot be added as a vendor."
            )

        # Check if already invited
        if EventVendor.objects.filter(event=event, invited_email=email, role=role).exists():
             raise serializers.ValidationError(
                f"This email has already been invited with the '{role}' role on this event."
            )
            
        try:
            vendor = User.objects.select_related("vendor_profile").get(email=email)
            
            if vendor.role != User.Role.VENDOR:
                raise serializers.ValidationError("This user is not registered as a vendor.")
            
            if not hasattr(vendor, "vendor_profile"):
                raise serializers.ValidationError("Vendor profile is missing for this user.")

            # Validate role dynamically
            if vendor.vendor_profile.subtype != role:
                raise serializers.ValidationError(
                    f"This vendor is registered as '{vendor.vendor_profile.subtype}' "
                    f"and cannot be assigned the role '{role}'."
                )
            
            if EventVendor.objects.filter(event=event, vendor=vendor, role=role).exists():
                raise serializers.ValidationError(f"This vendor already has the '{role}' role on this event.")
                
            attrs['vendor'] = vendor

        except User.DoesNotExist:
            # User doesn't exist, we will just record the email
            attrs['vendor'] = None

        return attrs

    def create(self, validated_data):
        event = self.context["event"]
        email = validated_data.pop("vendor_email")
        name = validated_data.pop("vendor_name", None)
        phone = validated_data.pop("vendor_phone", None)
        vendor = validated_data.pop("vendor", None)

        return EventVendor.objects.create(
            event=event,
            vendor=vendor,
            invited_email=email,
            invited_name=name,
            invited_phone=phone,
            is_confirmed=True,
            **validated_data
        )


class EventVendorDetailSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for displaying vendor details on an event.
    Used in list/retrieve responses.
    """
    vendor_username = serializers.SerializerMethodField()
    vendor_email = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    vendor_phone = serializers.SerializerMethodField()
    vendor_business_name = serializers.SerializerMethodField()
    vendor_is_verified = serializers.SerializerMethodField()

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
            "vendor_phone",
            "vendor_business_name",
            "vendor_is_verified",
        )
        read_only_fields = fields

    def get_vendor_username(self, obj):
        if obj.vendor:
            return obj.vendor.username
        return obj.invited_name or "Pending Registration"

    def get_role_display(self, obj):
        return obj.role.replace("_", " ").title() if obj.role else ""

    def get_vendor_email(self, obj):
        if obj.vendor:
            return obj.vendor.email
        return obj.invited_email

    def get_vendor_phone(self, obj):
        if obj.vendor and hasattr(obj.vendor, 'phone_number'):
            return obj.vendor.phone_number
        return obj.invited_phone or ""

    def get_vendor_business_name(self, obj):
        if obj.vendor and hasattr(obj.vendor, 'vendor_profile'):
            return obj.vendor.vendor_profile.service_title or obj.vendor.get_full_name() or obj.vendor.username
        return obj.invited_name or "Pending Registration"

    def get_vendor_is_verified(self, obj):
        if obj.vendor and hasattr(obj.vendor, 'vendor_profile'):
            return obj.vendor.vendor_profile.is_cac_verified
        return False


class VendorAcceptInviteSerializer(serializers.Serializer):
    """
    Used by the invited vendor to accept or decline.
    Accepts a boolean `accept` field alongside the invitation_code from the URL.
    """
    accept = serializers.BooleanField(
        help_text="Set to true to accept the invitation, false to decline."
    )

