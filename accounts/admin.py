#  accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    EventOwnerProfile,
    VendorProfile,
    AttendeeProfile,
)


# =========================================================
# SITE
# =========================================================
admin.site.site_header = "Neoevents Admin"
admin.site.site_title = "Neoevents Management"
admin.site.index_title = "Welcome to the Neoevents Management Area"


# =========================================================
# USER ADMIN
# =========================================================

@admin.register(User)
class CustomUserAdmin(UserAdmin):

    ordering = ("-date_joined",)

    list_display = ("id", "username", "email", "role", "is_active", "is_staff","date_joined",)

    list_filter = ("role", "is_active", "is_staff", "is_superuser",)

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    readonly_fields = (
        "date_joined",
        "last_login",
    )

    fieldsets = (

        ("Authentication", {
            "fields": (
                "username",
                "password",
            )
        }),

        ("Personal Information", {
            "fields": (
                "first_name",
                "last_name",
                "email",
                "phone_number",
            )
        }),

        ("Platform Access", {
            "fields": (
                "role",
                # "is_verified",
                "onboarding_status",
            )
        }),

        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Important Dates", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    add_fieldsets = (

        ("Create User", {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role", "is_active", "is_staff",),
        }),
    )


# =========================================================
# EVENT OWNER PROFILE ADMIN
# =========================================================

@admin.register(EventOwnerProfile)
class EventOwnerProfileAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "organisation_name",
        "is_business_verified",
        "total_events_created",
        "created_at",
    )

    list_filter = (
        "is_business_verified",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "organisation_name",
        "business_registration_number",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "total_events_created",
        "total_tickets_sold",
    )

    fieldsets = (

        ("User", {
            "fields": (
                "user",
            )
        }),

        ("Organisation Information", {
            "fields": (
                "organisation_name",
                "organisation_website",
                "organisation_logo",
            )
        }),

        ("Verification", {
            "fields": (
                "business_registration_number",
                "is_business_verified",
            )
        }),

        ("Payout Information", {
            "fields": (
                "payout_account_ref",
            )
        }),

        ("Platform Statistics", {
            "fields": (
                "total_events_created",
                "total_tickets_sold",
            )
        }),

        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )


# =========================================================
# VENDOR PROFILE ADMIN
# =========================================================

@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "subtype",
        "service_title",
        "years_of_experience",
        "is_available_for_hire",
        "average_rating",
        "created_at",
    )

    list_filter = (
        "subtype",
        "is_available_for_hire",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "service_title",
        "service_areas",
    )

    readonly_fields = (
        "average_rating",
        "total_reviews",
        "created_at",
        "updated_at",
    )

    fieldsets = (

        ("User Information", {
            "fields": (
                "user",
                "subtype",
            )
        }),

        ("Professional Information", {
            "fields": (
                "bio",
                "profile_image",
                "service_title",
                "years_of_experience",
                "service_areas",
            )
        }),

        ("Portfolio & Socials", {
            "fields": (
                "portfolio_website",
                "instagram_handle",
                "portfolio_cover",
            )
        }),

        ("Pricing", {
            "fields": (
                "base_rate",
                "rate_unit",
            )
        }),

        ("Availability", {
            "fields": (
                "is_available_for_hire",
                "booking_lead_days",
            )
        }),

        ("Ratings", {
            "fields": (
                "average_rating",
                "total_reviews",
            )
        }),

        ("Payout", {
            "fields": (
                "payout_account_ref",
            )
        }),

        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )


# =========================================================
# ATTENDEE PROFILE ADMIN
# =========================================================

@admin.register(AttendeeProfile)
class AttendeeProfileAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "full_name",
        "email",
        "phone_number",
        "registration_code",
    )

    search_fields = (
        "full_name",
        "email",
        "phone_number",
        "registration_code",
    )

    readonly_fields = (
        "registration_code",
    )

    fieldsets = (

        ("Attendee Information", {
            "fields": (
                "user",
                "full_name",
                "email",
                "phone_number",
            )
        }),

        ("Security & Access", {
            "fields": (
                "registration_code",
                "reference_image",
            )
        }),
    )
