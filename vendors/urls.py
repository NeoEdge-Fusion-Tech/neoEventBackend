from django.urls import path
from .views import (
    VendorBusinessDetailView,
    VendorGalleryCategoryListCreateView,
    VendorGalleryCategoryDetailView,
    VendorGalleryEventListCreateView,
    VendorGalleryEventDetailView,
    VendorGalleryListCreateView,
    VendorGalleryDetailView,
    VendorPublicProfileView
)

app_name = 'vendors'

urlpatterns = [
    path('business/', VendorBusinessDetailView.as_view(), name='business-detail'),
    path('categories/', VendorGalleryCategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<uuid:pk>/', VendorGalleryCategoryDetailView.as_view(), name='category-detail'),
    path('events/', VendorGalleryEventListCreateView.as_view(), name='event-list-create'),
    path('events/<uuid:pk>/', VendorGalleryEventDetailView.as_view(), name='event-detail'),
    path('gallery/', VendorGalleryListCreateView.as_view(), name='gallery-list-create'),
    path('gallery/<uuid:pk>/', VendorGalleryDetailView.as_view(), name='gallery-detail'),
    path('profile/<str:lookup>/', VendorPublicProfileView.as_view(), name='public-profile'),
]
