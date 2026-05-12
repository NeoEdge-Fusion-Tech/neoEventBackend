from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Event, EventVendor


class EventVendorInline(admin.TabularInline):
    """Allows managing vendors directly from the Event detail page."""
    model = EventVendor
    extra = 1
    autocomplete_fields = ['vendor']
    fields = ('vendor', 'role', 'is_confirmed', 'accepted_at')
    readonly_fields = ('accepted_at',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # List View Display
    list_display = (
        'title', 'owner', 'status_tag', 'start_date', 
        'is_public', 'vendor_count', 'created_at'
    )
    list_filter = ('status', 'is_public', 'start_date', 'created_at')
    search_fields = ('title', 'venue_name', 'owner__username', 'owner__email')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-created_at',)
    date_hierarchy = 'start_date' # Adds a drill-down navigation by date
    
    # Detail View Organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'owner', 'description', 'status', 'is_public')
        }),
        ('Venue & Media', {
            'fields': ('venue_name', 'venue_address', 'banner_image')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date', 'registration_deadline')
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('id', 'created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [EventVendorInline]

    # Custom Methods for Admin UI
    @admin.display(description='Status')
    def status_tag(self, obj):
        """Custom colored tags for event status."""
        colors = {
            'DRAFT': 'gray',
            'PUBLISHED': 'blue',
            'ACTIVE': 'green',
            'COMPLETED': 'black',
            'CANCELLED': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )

    def vendor_count(self, obj):
        """Shows how many vendors are attached to this event."""
        return obj.vendors.count()
    vendor_count.short_description = "Vendors"

@admin.register(EventVendor)
class EventVendorAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'event', 'role', 'is_confirmed', 'invited_at')
    list_filter = ('role', 'is_confirmed')
    search_fields = ('vendor__username', 'event__title')
    autocomplete_fields = ['event', 'vendor'] # Better for large datasets
    
    actions = ['mark_as_confirmed']

    @admin.action(description='Manually confirm selected vendors')
    def mark_as_confirmed(self, request, queryset):
        queryset.update(is_confirmed=True, accepted_at=timezone.now())
