# utils/permissions.py
from rest_framework.permissions import BasePermission
from ..models import User

class IsAdminUser(BasePermission):
    """Internal Admin check (Global)"""
    message = "Access denied. Internal Admin only."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin_user)

class IsOpsAdmin(BasePermission):
    """Strict Ops check"""
    message = "Only Operations admins can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_ops_admin)

class IsCustomerAdmin(BasePermission):
    """Strict Customer check"""
    message = "Only Customer Support admins can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_customer_admin)
    

class IsOwnerUser(BasePermission):
    """Grants access only to Event Owners."""

    message = "You must be an Event Owner to perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_event_owner)


class IsVendorUser(BasePermission):
    """Grants access only to Event Vendors."""

    message = "You must be a registered Vendor to perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_vendor)


class IsApprovedOwnerOrVendor(BasePermission):
    """
    Grants access to OWNER or VENDOR accounts that have been approved by ops.
    Use this on endpoints that require a vetted account (e.g. creating events).
    """

    message = "Your account is pending approval. Please wait for an ops admin to review it."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.role in (user.Role.OWNER, user.Role.VENDOR):
            return user.is_approved
        # ADMINs and ATTENDEEs pass through (handled by other permissions)
        return True


class IsAttendee(BasePermission):
    """Grants access only to Attendees."""

    message = "This action is reserved for event attendees."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_attendee)


class IsOwnerOrAdmin(BasePermission):
    """Grants access to Event Owners or Internal Admins."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and (user.is_event_owner or user.is_admin_user)
        )
