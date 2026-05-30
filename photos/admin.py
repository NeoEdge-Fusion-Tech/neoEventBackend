from django.contrib import admin
from .models.photo import Photo, PhotoFace, UserPhoto

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'uploader', 'ai_status', 'created_at')
    list_filter = ('ai_status', 'is_public', 'created_at')
    search_fields = ('event__title', 'uploader__email', 'id')
    readonly_fields = ('created_at',)

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
