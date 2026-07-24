from django.urls import path


from .views import (
    EventListView,
    EventDetailView,
    EventCreateView,
    EventUpdateView,
    EventDeleteView,
    EventPresignedUploadUrlView,
    OwnerEventListView,
    EventTriggerClassificationView,
    DuplicateEventView,
    BroadcastMessageCreateView,
    BroadcastMessageListView,

    VendorInviteView,
    EventVendorListView,
    VendorRemoveView,
    VendorRespondToInviteView,
    VendorSetupPasswordView,
    MyVendorAssignmentsView,
    InvitedEventMediaUploadView,
    InvitedEventMediaDeleteView,
    VendorTypesView,
    RateVendorView,
    VendorEventRatingsListView,
    
    ValidatorLoginView,
    ValidatorOnboardingView,
    ValidatorEventListView,
)

urlpatterns = [

    path("events/", EventListView.as_view(), name="event-list-base",),
    path("events/all/", EventListView.as_view(), name="event-list",),
    path("events/mine/", OwnerEventListView.as_view(), name="event-list-mine",),
    path("events/create/", EventCreateView.as_view(), name="event-create",),
    path("events/generate-presigned-url/", EventPresignedUploadUrlView.as_view(), name="event-generate-presigned-url",),

    # ── Validator APIs ───────────────────────────────────────────────────
    path("events/validator-list/", ValidatorEventListView.as_view(), name="validator-event-list"),

    path("events/<slug:slug>/", EventDetailView.as_view(), name="event-detail",),
    path("events/<uuid:id>/update/", EventUpdateView.as_view(), name="event-update",),
    path("events/<uuid:id>/delete/", EventDeleteView.as_view(), name="event-delete",),
    path("events/<uuid:id>/duplicate/", DuplicateEventView.as_view(), name="event-duplicate",),
    path("events/<uuid:id>/trigger-classification/", EventTriggerClassificationView.as_view(), name="event-trigger-classification",),
    path("events/<uuid:id>/broadcasts/", BroadcastMessageListView.as_view(), name="event-broadcasts-list",),
    path("events/<uuid:id>/broadcasts/send/", BroadcastMessageCreateView.as_view(), name="event-broadcast-send",),

    # List all vendors (pending + confirmed) on an event
    path("events/<uuid:event_id>/vendors/",EventVendorListView.as_view(), name="event-vendor-list",),
    path("events/vendors/types/", VendorTypesView.as_view(), name="vendor-types"),

    # Invite a new vendor to an event
    path("events/<uuid:event_id>/vendors/invite/", VendorInviteView.as_view(), name="event-vendor-invite",),

    # Remove a specific vendor assignment from an event
    path("events/<uuid:event_id>/vendors/<uuid:vendor_assignment_id>/remove/", VendorRemoveView.as_view(), name="event-vendor-remove",),

    # ── Vendor: respond to invitation & view own assignments ─────────────────

    # Accept or decline an invitation using the unique code
    path("events/invitations/<uuid:invitation_code>/setup/", VendorSetupPasswordView.as_view(), name="vendor-setup-password",),
    path("events/invitations/<uuid:invitation_code>/respond/", VendorRespondToInviteView.as_view(), name="vendor-respond-invite",),

    # Vendor's personal dashboard of all their assignments
    path("events/vendors/my-assignments/", MyVendorAssignmentsView.as_view(), name="vendor-my-assignments",),
    path("events/vendors/assignments/<uuid:assignment_id>/media/", InvitedEventMediaUploadView.as_view(), name="invited-event-media-upload",),
    path("events/vendors/media/<uuid:pk>/", InvitedEventMediaDeleteView.as_view(), name="invited-event-media-delete",),

    # Ratings
    path("events/<uuid:event_id>/vendors/<uuid:vendor_id>/rate/", RateVendorView.as_view(), name="rate-vendor",),
    path("events/<uuid:event_id>/vendors/<uuid:vendor_id>/ratings/", VendorEventRatingsListView.as_view(), name="vendor-ratings",),

    # ── Validator Auth APIs ──────────────────────────────────────────────
    path("auth/validator/login/", ValidatorLoginView.as_view(), name="validator-login"),
    path("auth/validator/onboard/", ValidatorOnboardingView.as_view(), name="validator-onboard"),
]
