# # tickets/urls.py
from django.urls import path

from .views import (
    EventTicketTypeListView,
    EventRegistrationCreateView,
    RegistrationDetailView,
    EventCheckInView
)


urlpatterns = [

    path(
        "events/<uuid:event_id>/tickets/",
        EventTicketTypeListView.as_view(),
        name="event-ticket-types",
    ),

    path(
        "register/",
        EventRegistrationCreateView.as_view(),
        name="event-register",
    ),

    path(
        "registrations/<uuid:registration_code>/",
        RegistrationDetailView.as_view(),
        name="registration-detail",
    ),

    path(
    "check-in/<uuid:registration_code>/",
    EventCheckInView.as_view(),
    name="event-check-in",
),
]

# from django.urls import path
# from .views import RegistrationListCreateView, TicketDetailView

# urlpatterns = [
#     path('registrations/', RegistrationListCreateView.as_view(), name='registration-list'),
#     path('tickets/<int:reg_id>/', TicketDetailView.as_view(), name='ticket-detail'),
# ]

