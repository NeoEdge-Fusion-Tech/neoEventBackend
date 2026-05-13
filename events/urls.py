from django.urls import path


from .views import (
    EventListView,
    EventDetailView,
    EventCreateView,
    EventUpdateView,
    # EventDeleteView,
    # OwnerEventListView,

    VendorInviteView,
    EventVendorListView,
    VendorRemoveView,
    VendorRespondToInviteView,
    MyVendorAssignmentsView,
)

urlpatterns = [

    path("events/all/", EventListView.as_view(), name="event-list",),
    path("events/create/", EventCreateView.as_view(), name="event-create",),

    path("events/<slug:slug>/", EventDetailView.as_view(), name="event-detail",),
    path("events/<uuid:id>/update/", EventUpdateView.as_view(), name="event-update", ),

    # List all vendors (pending + confirmed) on an event
    path("events/<uuid:event_id>/vendors/",EventVendorListView.as_view(), name="event-vendor-list",),

    # Invite a new vendor to an event
    path("events/<uuid:event_id>/vendors/invite/", VendorInviteView.as_view(), name="event-vendor-invite",),

    # Remove a specific vendor assignment from an event
    path("events/<uuid:event_id>/vendors/<uuid:vendor_assignment_id>/remove/", VendorRemoveView.as_view(), name="event-vendor-remove",),

    # ── Vendor: respond to invitation & view own assignments ─────────────────

    # Accept or decline an invitation using the unique code
    path("events/invitations/<uuid:invitation_code>/respond/", VendorRespondToInviteView.as_view(), name="vendor-respond-invite",),

    # Vendor's personal dashboard of all their assignments
    path("events/vendors/my-assignments/", MyVendorAssignmentsView.as_view(), name="vendor-my-assignments",),
]

