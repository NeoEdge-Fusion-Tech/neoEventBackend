from django.contrib import admin
from .models import VendorBusiness, VendorGalleryCategory, VendorGalleryEvent, VendorGallery

@admin.register(VendorBusiness)
class VendorBusinessAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'is_registered', 'country_of_registration')
    search_fields = ('business_name', 'user__username', 'user__email')

@admin.register(VendorGalleryCategory)
class VendorGalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor')
    search_fields = ('name', 'vendor__business_name')

@admin.register(VendorGalleryEvent)
class VendorGalleryEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'date')
    search_fields = ('name', 'category__name')

@admin.register(VendorGallery)
class VendorGalleryAdmin(admin.ModelAdmin):
    list_display = ('event', 'file_type', 'created_at')
    list_filter = ('file_type',)
