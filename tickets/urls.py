# # tickets/urls.py
from django.urls import path

from .views import (
    EventTicketTypeListView,
    EventRegistrationCreateView,
    RegistrationDetailView,
    EventRegistrationsListView,
    EventCheckInView,
    MyUpcomingEventsView,
    MyPastEventsView,
    MyRegistrationDetailView,
    CancelRegistrationView,
    MyActiveTicketsView,
    MyAttendeeProfileView,
    EventExportView,
    ValidatorCheckInView,
    generate_badge_html,
)


urlpatterns = [

    path("tickets/events/<uuid:event_id>/tickets/",
        EventTicketTypeListView.as_view(),
        name="event-ticket-types-plural",
    ),
    path("event/<uuid:event_id>/tickets/",
        EventTicketTypeListView.as_view(),
        name="event-ticket-types",
    ),

    path("tickets/register/", EventRegistrationCreateView.as_view(),
        name="event-register-prefix",
    ),
    path("register/", EventRegistrationCreateView.as_view(),
        name="event-register",
    ),

    path("tickets/events/<uuid:event_id>/registrations/", EventRegistrationsListView.as_view(), name="event-registrations-list-prefix",),
    path("events/<uuid:event_id>/registrations/", EventRegistrationsListView.as_view(), name="event-registrations-list",),
    path("events/<uuid:event_id>/export/", EventExportView.as_view(), name="event-export"),

    path("registrations/<str:registration_code>/", RegistrationDetailView.as_view(), name="registration-detail",),

    path("check-in/<str:registration_code>/", EventCheckInView.as_view(), name="event-check-in",),
    
    path("attendee/events/upcoming/", MyUpcomingEventsView.as_view(), name="attendee-upcoming-events",),
    
    path("attendee/events/history/", MyPastEventsView.as_view(), name="attendee-event-history",),

    path("attendee/registrations/<str:registration_code>/", MyRegistrationDetailView.as_view(), name="attendee-registration-detail",),

    path("attendee/registrations/<uuid:id>/cancel/", CancelRegistrationView.as_view(), name="cancel-registration",),

    path('attendee/tickets/active/', MyActiveTicketsView.as_view(), name='active-tickets'),
    
    path('me/attendee-profile/', MyAttendeeProfileView.as_view(), name='attendee-profile'),

    # ── Validator App Endpoints ────────────────────────────────────────────────
    path("tickets/validator/checkin/", ValidatorCheckInView.as_view(), name="validator-check-in"),
    path("tickets/badge/<str:registration_code>/", generate_badge_html, name="badge-generate"),
]

