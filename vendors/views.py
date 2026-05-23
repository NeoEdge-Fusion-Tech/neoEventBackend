from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import VendorBusiness, VendorGalleryCategory, VendorGalleryEvent, VendorGallery
from .serializers import (
    VendorBusinessSerializer, 
    VendorGalleryCategorySerializer, 
    VendorGalleryEventSerializer, 
    VendorGallerySerializer,
    VendorPublicProfileSerializer
)

class VendorPermissionMixin:
    def get_vendor_business(self):
        try:
            return self.request.user.vendor_business
        except VendorBusiness.DoesNotExist:
            raise PermissionDenied("User is not a vendor.")

class VendorBusinessDetailView(generics.RetrieveUpdateAPIView, VendorPermissionMixin):
    serializer_class = VendorBusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.get_vendor_business()

class VendorGalleryCategoryListCreateView(generics.ListCreateAPIView, VendorPermissionMixin):
    serializer_class = VendorGalleryCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        vendor = self.get_vendor_business()
        return VendorGalleryCategory.objects.filter(vendor=vendor)

    def perform_create(self, serializer):
        vendor = self.get_vendor_business()
        serializer.save(vendor=vendor)

class VendorGalleryCategoryDetailView(generics.RetrieveUpdateDestroyAPIView, VendorPermissionMixin):
    serializer_class = VendorGalleryCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        vendor = self.get_vendor_business()
        return VendorGalleryCategory.objects.filter(vendor=vendor)

class VendorGalleryEventListCreateView(generics.ListCreateAPIView, VendorPermissionMixin):
    serializer_class = VendorGalleryEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        vendor = self.get_vendor_business()
        return VendorGalleryEvent.objects.filter(category__vendor=vendor)

class VendorGalleryEventDetailView(generics.RetrieveUpdateDestroyAPIView, VendorPermissionMixin):
    serializer_class = VendorGalleryEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        vendor = self.get_vendor_business()
        return VendorGalleryEvent.objects.filter(category__vendor=vendor)

class VendorGalleryListCreateView(generics.ListCreateAPIView, VendorPermissionMixin):
    serializer_class = VendorGallerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        vendor = self.get_vendor_business()
        return VendorGallery.objects.filter(event__category__vendor=vendor)

class VendorGalleryDetailView(generics.RetrieveUpdateDestroyAPIView, VendorPermissionMixin):
    serializer_class = VendorGallerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        vendor = self.get_vendor_business()
        return VendorGallery.objects.filter(event__category__vendor=vendor)

class VendorPublicProfileView(generics.RetrieveAPIView):
    queryset = VendorBusiness.objects.all()
    serializer_class = VendorPublicProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'
