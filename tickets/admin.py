from django.contrib import admin
from django.utils.html import format_html
from .models import (
    EventRegistration, 
    TicketType,
    DailyCheckIn
)


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'formatted_price', 'inventory_status', 'is_active')
    list_filter = ('is_active', 'event')
    search_fields = ('name', 'event__title')
    autocomplete_fields = ['event']
    
    @admin.display(description='Price')
    def formatted_price(self, obj):
        return f"${obj.price}"

    @admin.display(description='Inventory')
    def inventory_status(self, obj):
        """Shows progress of tickets sold vs total quantity."""
        remaining = obj.remaining
        color = "green" if remaining > (obj.quantity * 0.2) else "red"
        return format_html(
            '<b>{} / {}</b> ( <span style="color: {};">{} left</span> )',
            obj.sold_count, obj.quantity, color, remaining
        )

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'registration_code_short', 'attendee', 'event', 
        'ticket_type', 'status_badge', 'checked_in_icon', 'registered_at'
    )
    list_filter = ('status', 'checked_in', 'event', 'ticket_type')
    search_fields = (
        'registration_code', 
        'attendee__user__email', 
        'attendee__user__username',
        'event__title'
    )
    readonly_fields = ('registration_code', 'qr_code_preview', 'registered_at')
    autocomplete_fields = ['event', 'attendee', 'ticket_type']
    
    actions = ['mark_as_checked_in', 'cancel_registrations']

    # --- Custom Displays ---

    @admin.display(description='Code')
    def registration_code_short(self, obj):
        return str(obj.registration_code)[:8].upper()

    @admin.display(description='Checked In')
    def checked_in_icon(self, obj):
        if obj.checked_in:
            return format_html('<span style="color: green; font-size: 1.2em;">{}</span>', '✔')
        return format_html('<span style="color: #ccc; font-size: 1.2em;">{}</span>', '✘')

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'PENDING': '#f39c12',  # Orange
            'CONFIRMED': '#27ae60', # Green
            'CHECKED_IN': '#2980b9', # Blue
            'CANCELLED': '#c0392b', # Red
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.85em;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="150" height="150" />', obj.qr_code.url)
        return "No QR Code generated"

    # --- Custom Actions ---

    @admin.action(description="Check-in selected attendees")
    def mark_as_checked_in(self, request, queryset):
        updated = queryset.update(checked_in=True, status=EventRegistration.Status.CHECKED_IN)
        self.message_user(request, f"{updated} registrations successfully checked in.")

    @admin.action(description="Cancel selected registrations")
    def cancel_registrations(self, request, queryset):
        queryset.update(status=EventRegistration.Status.CANCELLED)

@admin.register(DailyCheckIn)
class DailyCheckInAdmin(admin.ModelAdmin):
    list_display = ('id', 'registration', 'date', 'time', 'device_id')
    list_filter = ('date',)
    search_fields = ('registration__registration_code', 'device_id')
    readonly_fields = ('id', 'time')
    autocomplete_fields = ['registration']
