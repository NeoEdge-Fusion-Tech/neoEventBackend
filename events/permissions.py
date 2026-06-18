# permissions.py
from rest_framework.permissions import BasePermission

class IsEventOwnerRole(BasePermission):
    """
    Event owners may manage events. The platform super admin (role=ADMIN)
    is always let through too, regardless of who owns the event.
    """

    message = "Only the event's owner or an admin can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role in (user.Role.OWNER, user.Role.ADMIN)
        )

    def has_object_permission(self, request, view, obj):
        # obj is the Event instance — only its owner, or the super admin, may write/delete it
        user = request.user
        return user.role == user.Role.ADMIN or obj.owner == user