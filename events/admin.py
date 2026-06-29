from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Event, EventVendor, InvitedEventMedia


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
        'is_public', 'vendor_count', 'attendees_notified_at', 'created_at'
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
            'fields': ('id', 'attendees_notified_at', 'created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [EventVendorInline]
    actions = ['retry_ai_processing', 'notify_attendees']

    @admin.action(description="Notify Attendees for selected events")
    def notify_attendees(self, request, queryset):
        from core.sqs import dispatch_task
        from django.utils import timezone
        
        for event in queryset:
            dispatch_task("notify_users_of_mapped_gallery", {"event_id": str(event.id)})
            
        queryset.update(attendees_notified_at=timezone.now())
        self.message_user(request, f"Triggered notification for attendees in {queryset.count()} events.")

    @admin.action(description='Retry AI processing for all pending/failed photos in selected events')
    def retry_ai_processing(self, request, queryset):
        from photos.models.photo import Photo
        from photos.tasks import extract_faces_from_photos
        
        event_ids = list(queryset.values_list('id', flat=True))
        photos = Photo.objects.filter(
            event_id__in=event_ids,
            ai_status__in=[Photo.AIProcessingStatus.PENDING, Photo.AIProcessingStatus.FAILED]
        )
        photo_ids = list(photos.values_list('id', flat=True))
        
        if not photo_ids:
            self.message_user(request, "No pending or failed photos found for the selected events.", level="WARNING")
            return
            
        # Batch in groups of 50
        batch_size = 50
        for i in range(0, len(photo_ids), batch_size):
            batch = [str(pid) for pid in photo_ids[i:i + batch_size]]
            extract_faces_from_photos.delay(batch)
            
        self.message_user(request, f"Triggered AI processing for {len(photo_ids)} photos across {queryset.count()} events.")

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


@admin.register(InvitedEventMedia)
class InvitedEventMediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_vendor', 'is_processed', 'uploaded_at')
    list_filter = ('is_processed', 'uploaded_at')
    search_fields = ('event_vendor__vendor__username', 'event_vendor__vendor__email', 'event_vendor__event__title')
    readonly_fields = ('id', 'uploaded_at')
    autocomplete_fields = ['event_vendor']
