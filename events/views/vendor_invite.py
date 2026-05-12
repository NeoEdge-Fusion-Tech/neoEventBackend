# events/views/vendor_invite.py
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from drf_spectacular.utils import extend_schema

from ..models import Event, EventVendor
from ..serializers import (
    VendorInviteSerializer,
    EventVendorDetailSerializer,
    VendorAcceptInviteSerializer,
)
from ..permissions import IsEventOwnerRole


# ------------------------------------------------
# Owner-facing views (manage vendors on their event)
# -------------------------------------------

@extend_schema(
    tags=["Event Vendors"],
    summary="Invite a vendor to an event",
    description=(
        "Allows the event owner to invite a registered user as a vendor "
        "by their email address. A unique invitation code is generated and "
        "the vendor must accept before they are confirmed on the event. "
        "The same vendor can hold multiple roles on the same event, but "
        "not the same role twice."
    ),
)
class VendorInviteView(generics.CreateAPIView):
    """
    POST /events/<event_id>/vendors/invite/

    Owner sends { vendor_email, role }.
    Returns the created EventVendor with its invitation_code so the owner
    can forward the acceptance link to the vendor out-of-band (email, etc.).
    """
    serializer_class = VendorInviteSerializer
    permission_classes = [IsAuthenticated, IsEventOwnerRole]

    def get_object(self):
        try:
            event = Event.objects.get(id=self.kwargs["event_id"])
        except Event.DoesNotExist:
            raise NotFound("Event not found.")
        self.check_object_permissions(self.request, event)
        return event

    def create(self, request, *args, **kwargs):
        event = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "event": event},
        )
        serializer.is_valid(raise_exception=True)
        vendor_assignment = serializer.save()

        # Return full detail so the owner sees the invitation_code
        response_data = {
            "id": str(vendor_assignment.id),
            "event": str(event.id),
            "event_title": event.title,
            "vendor_username": vendor_assignment.vendor.username,
            "vendor_email": vendor_assignment.vendor.email,
            "role": vendor_assignment.role,
            "invitation_code": str(vendor_assignment.invitation_code),
            "is_confirmed": vendor_assignment.is_confirmed,
            "invited_at": vendor_assignment.invited_at,
            "message": (
                f"Invitation sent. Share this code with the vendor: "
                f"{vendor_assignment.invitation_code}"
            ),
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Event Vendors"],
    summary="List vendors on an event",
    description=(
        "Returns all vendor assignments for a given event. "
        "Only the event owner can view this list. "
        "Includes both confirmed and pending (unconfirmed) vendors."
    ),
)
class EventVendorListView(generics.ListAPIView):
    """
    GET /events/<event_id>/vendors/

    Owner views all vendors (confirmed + pending) on their event.
    """
    serializer_class = EventVendorDetailSerializer
    permission_classes = [IsAuthenticated, IsEventOwnerRole]

    def get_event(self):
        try:
            event = Event.objects.get(id=self.kwargs["event_id"])
        except Event.DoesNotExist:
            raise NotFound("Event not found.")
        self.check_object_permissions(self.request, event)
        return event

    def get_queryset(self):
        event = self.get_event()
        return EventVendor.objects.filter(event=event).select_related("vendor")


@extend_schema(
    tags=["Event Vendors"],
    summary="Remove a vendor from an event",
    description=(
        "Allows the event owner to remove a vendor assignment entirely "
        "(whether confirmed or still pending). "
        "Uses the EventVendor UUID, not the user ID."
    ),
)
class VendorRemoveView(generics.DestroyAPIView):
    """
    DELETE /events/<event_id>/vendors/<vendor_assignment_id>/remove/

    Owner removes a vendor (pending or confirmed).
    """
    permission_classes = [IsAuthenticated, IsEventOwnerRole]
    lookup_field = "id"

    def get_event(self):
        try:
            event = Event.objects.get(id=self.kwargs["event_id"])
        except Event.DoesNotExist:
            raise NotFound("Event not found.")
        self.check_object_permissions(self.request, event)
        return event

    def get_object(self):
        event = self.get_event()
        try:
            return EventVendor.objects.get(
                id=self.kwargs["vendor_assignment_id"],
                event=event,
            )
        except EventVendor.DoesNotExist:
            raise NotFound("Vendor assignment not found on this event.")

    def destroy(self, request, *args, **kwargs):
        vendor_assignment = self.get_object()
        vendor_username = vendor_assignment.vendor.username
        vendor_assignment.delete()
        return Response(
            {"message": f"Vendor '{vendor_username}' has been removed from the event."},
            status=status.HTTP_200_OK,
        )


# ----------------------------------------------
# Vendor-facing views (accept or decline an invitation)
# -------------------------------------------

@extend_schema(
    tags=["Event Vendors"],
    summary="Accept or decline a vendor invitation",
    description=(
        "Allows the invited vendor to accept or decline their invitation "
        "using the unique invitation_code sent to them by the event owner. "
        "Only the vendor the invitation was issued to can respond — "
        "any other authenticated user will receive a 403."
        "\n\n"
        "**Accept**: `{ \"accept\": true }` → marks `is_confirmed = true`.\n\n"
        "**Decline**: `{ \"accept\": false }` → deletes the invitation record."
    ),
)
class VendorRespondToInviteView(APIView):
    """
    POST /vendors/invitations/<invitation_code>/respond/

    The invited vendor accepts or declines using their unique code.
    This endpoint is intentionally NOT nested under /events/<event_id>/
    so the vendor only needs their invitation code — no need to know the
    event UUID up front.
    """
    permission_classes = [IsAuthenticated]

    def get_invitation(self, invitation_code):
        try:
            return EventVendor.objects.select_related(
                "vendor", "event"
            ).get(invitation_code=invitation_code)
        except EventVendor.DoesNotExist:
            raise NotFound("Invitation not found. The code may be invalid or expired.")

    def post(self, request, invitation_code):
        invitation = self.get_invitation(invitation_code)

        # Only the vendor the invite was issued to can respond
        if invitation.vendor != request.user:
            raise PermissionDenied(
                "You are not the recipient of this invitation."
            )

        # Prevent responding to an already-confirmed invitation
        if invitation.is_confirmed:
            return Response(
                {"detail": "This invitation has already been accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = VendorAcceptInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["accept"]:
            invitation.is_confirmed = True
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=["is_confirmed", "accepted_at"])

            return Response(
                {
                    "message": (
                        f"You have successfully joined '{invitation.event.title}' "
                        f"as {invitation.get_role_display()}."
                    ),
                    "event_id": str(invitation.event.id),
                    "event_title": invitation.event.title,
                    "role": invitation.role,
                },
                status=status.HTTP_200_OK,
            )
        else:
            # Vendor declined — remove the record cleanly
            event_title = invitation.event.title
            invitation.delete()
            return Response(
                {"message": f"You have declined the invitation for '{event_title}'."},
                status=status.HTTP_200_OK,
            )


@extend_schema(
    tags=["Event Vendors"],
    summary="List my vendor assignments",
    description=(
        "Returns all event vendor assignments for the currently authenticated user, "
        "both confirmed and pending. Useful for a vendor's dashboard."
    ),
)
class MyVendorAssignmentsView(generics.ListAPIView):
    """
    GET /vendors/my-assignments/

    A vendor can see all events they have been invited to (any status).
    """
    serializer_class = EventVendorDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            EventVendor.objects.filter(vendor=self.request.user)
            .select_related("event", "vendor")
            .order_by("-invited_at")
        )
    
