# from django.urls import path
# from .views import (
#     PhotoUploadView, 
#     UserGalleryView, 
#     PhotographerPhotoListView, 
#     PhotoDeleteView,
#     UserPhotoCountView
# )

# urlpatterns = [
#     path('upload/', PhotoUploadView.as_view(), name='photo-upload'),
#     path('gallery/', UserGalleryView.as_view(), name='user-gallery'),
#     path('stats/count/', UserPhotoCountView.as_view(), name='photo-count'),
#     path('my-uploads/', PhotographerPhotoListView.as_view(), name='photographer-photos'),
#     path('delete/<int:pk>/', PhotoDeleteView.as_view(), name='photo-delete'),
# ]


from django.urls import path

from .views import (
    PhotoUploadView,
    PhotoListView,
    EventGalleryView,
    PersonalGalleryZipView,
    NotifyAttendeesView,
)

urlpatterns = [

    path(
        "events/<uuid:event_id>/upload/",
        PhotoUploadView.as_view(),
        name="event-photo-upload",
    ),

    path(
        "events/<uuid:event_id>/",
        PhotoListView.as_view(),
        name="event-photo-list",
    ),

    path(
        "gallery/",
        EventGalleryView.as_view(),
        name="event-gallery",
    ),

    path(
        "events/<uuid:event_id>/download-personal-zip/",
        PersonalGalleryZipView.as_view(),
        name="download-personal-zip",
    ),

    path(
        "events/<uuid:event_id>/notify-attendees/",
        NotifyAttendeesView.as_view(),
        name="notify-attendees",
    ),
]