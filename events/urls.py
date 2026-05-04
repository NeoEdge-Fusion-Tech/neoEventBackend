from django.urls import path

from .views import (
    EventListView,
    EventDetailView,
    EventCreateView,
    EventUpdateView,
    # EventDeleteView,
    # OwnerEventListView,
)

urlpatterns = [

    path(
        "",
        EventListView.as_view(),
        name="event-list",
    ),

    # path(
    #     "my-events/",
    #     OwnerEventListView.as_view(),
    #     name="owner-events",
    # ),

    path(
        "create/",
        EventCreateView.as_view(),
        name="event-create",
    ),

    path(
        "<slug:slug>/",
        EventDetailView.as_view(),
        name="event-detail",
    ),

    path(
        "<uuid:id>/update/",
        EventUpdateView.as_view(),
        name="event-update",
    ),

    # path(
    #     "<uuid:id>/delete/",
    #     EventDeleteView.as_view(),
    #     name="event-delete",
    # ),
]


# from django.urls import path
# from .views import (
#     EventListCreateView, 
#     EventDetailView, 
#     AssignedEventListView,
#     OwnedEventListView,
#     EventPhotographerCreateView, 
#     PhotographerEventDetailView
# )

# urlpatterns = [
#     path('', EventListCreateView.as_view(), name='event-list'),
#     path('owned/', OwnedEventListView.as_view(), name='owned-events'),
#     path('<int:pk>/', EventDetailView.as_view(), name='event-detail'),
#     path('assigned/', AssignedEventListView.as_view(), name='assigned-events'),
#     path('photographer/invite/', EventPhotographerCreateView.as_view(), name='photographer-invite'),
#     path('photographer/verify/<uuid:unique_code>/', PhotographerEventDetailView.as_view(), name='photographer-verify'),
# ]
