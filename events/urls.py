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

    path(
        "",
        EventListView.as_view(), name="event-list",
    ),

    # path(
    #     "my-events/",
    #     OwnerEventListView.as_view(),
    #     name="owner-events",
    # ),

    path(
        "create/", EventCreateView.as_view(), name="event-create",),

    path(
        "<slug:slug>/", EventDetailView.as_view(), name="event-detail",),

    path("<uuid:id>/update/", EventUpdateView.as_view(), name="event-update", ),

    # path(
    #     "<uuid:id>/delete/",
    #     EventDeleteView.as_view(),
    #     name="event-delete",
    # ),


    # List all vendors (pending + confirmed) on an event
    path(
        "<uuid:event_id>/vendors/",
        EventVendorListView.as_view(),
        name="event-vendor-list",
    ),

    # Invite a new vendor to an event
    path(
        "<uuid:event_id>/vendors/invite/",
        VendorInviteView.as_view(),
        name="event-vendor-invite",
    ),

    # Remove a specific vendor assignment from an event
    path(
        "<uuid:event_id>/vendors/<uuid:vendor_assignment_id>/remove/",
        VendorRemoveView.as_view(),
        name="event-vendor-remove",
    ),

    # ── Vendor: respond to invitation & view own assignments ─────────────────

    # Accept or decline an invitation using the unique code
    path(
        "invitations/<uuid:invitation_code>/respond/",
        VendorRespondToInviteView.as_view(),
        name="vendor-respond-invite",
    ),

    # Vendor's personal dashboard of all their assignments
    path(
        "vendors/my-assignments/",
        MyVendorAssignmentsView.as_view(),
        name="vendor-my-assignments",
    ),
]

