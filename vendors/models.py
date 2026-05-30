import uuid
from django.db import models
from django.conf import settings
from core.models import UUIDPkField

class VendorBusiness(UUIDPkField):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vendor_business')
    business_name = models.CharField(max_length=255)
    is_registered = models.BooleanField(default=False)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    country_of_registration = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True, null=True)
    state_or_county = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return self.business_name

class VendorGalleryCategory(UUIDPkField):
    vendor = models.ForeignKey(VendorBusiness, on_delete=models.CASCADE, related_name='gallery_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('vendor', 'name')

    def __str__(self):
        return f"{self.vendor.business_name} - {self.name}"

class VendorGalleryEvent(UUIDPkField):
    category = models.ForeignKey(VendorGalleryCategory, on_delete=models.CASCADE, related_name='events')
    system_event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, blank=True, null=True, related_name='vendor_galleries')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

class VendorGallery(UUIDPkField):
    class FileType(models.TextChoices):
        IMAGE = 'IMAGE', 'Image'
        VIDEO = 'VIDEO', 'Video'

    event = models.ForeignKey(VendorGalleryEvent, on_delete=models.CASCADE, related_name='media')
    media_file = models.FileField(upload_to='vendor_gallery/%Y/%m/%d/')
    file_type = models.CharField(max_length=10, choices=FileType.choices, default=FileType.IMAGE)
    caption = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.event.name} - {self.file_type}"
