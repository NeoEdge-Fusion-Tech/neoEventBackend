from django.contrib import admin
from .models.photo import Photo, PhotoFace, UserPhoto

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'uploader', 'ai_status', 'created_at')
    list_filter = ('ai_status', 'is_public', 'created_at')
    search_fields = ('event__title', 'uploader__email', 'id')
    readonly_fields = ('created_at',)
    actions = ['retry_ai_processing']

    @admin.action(description="Retry AI Processing for selected photos")
    def retry_ai_processing(self, request, queryset):
        from .tasks import extract_faces_from_photos
        # Only retry pending or failed photos
        valid_photos = queryset.filter(
            ai_status__in=[Photo.AIProcessingStatus.PENDING, Photo.AIProcessingStatus.FAILED]
        )
        photo_ids = list(valid_photos.values_list('id', flat=True))
        
        if not photo_ids:
            self.message_user(request, "No pending or failed photos selected.", level="WARNING")
            return
            
        # Batch in groups of 50
        batch_size = 50
        for i in range(0, len(photo_ids), batch_size):
            batch = [str(pid) for pid in photo_ids[i:i + batch_size]]
            extract_faces_from_photos.delay(batch)
            
        self.message_user(request, f"Triggered AI processing for {len(photo_ids)} photos.")

@admin.register(PhotoFace)
class PhotoFaceAdmin(admin.ModelAdmin):
    list_display = ('id', 'photo', 'confidence')
    search_fields = ('photo__id',)
    readonly_fields = ('id', 'photo', 'face_embedding', 'bounding_box', 'confidence')

@admin.register(UserPhoto)
class UserPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event', 'photo', 'confidence_score', 'source', 'created_at')
    list_filter = ('source', 'created_at')
    search_fields = ('user__email', 'event__title', 'photo__id')
    readonly_fields = ('created_at',)
