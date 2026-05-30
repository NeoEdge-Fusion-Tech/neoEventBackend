from rest_framework import serializers
from .models import VendorBusiness, VendorGalleryCategory, VendorGalleryEvent, VendorGallery

class VendorBusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorBusiness
        fields = '__all__'
        read_only_fields = ('user', 'id', 'created_at', 'updated_at')

class VendorGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorGallery
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class VendorGalleryEventSerializer(serializers.ModelSerializer):
    media = VendorGallerySerializer(many=True, read_only=True)
    
    class Meta:
        model = VendorGalleryEvent
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class VendorGalleryCategorySerializer(serializers.ModelSerializer):
    events = VendorGalleryEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = VendorGalleryCategory
        fields = '__all__'
        read_only_fields = ('vendor', 'id', 'created_at', 'updated_at')

class VendorPublicProfileSerializer(serializers.ModelSerializer):
    gallery_categories = VendorGalleryCategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = VendorBusiness
        fields = ['id', 'business_name', 'address', 'city', 'state_or_county', 'country', 'email', 'phone_number', 'gallery_categories', 'custom_url']
