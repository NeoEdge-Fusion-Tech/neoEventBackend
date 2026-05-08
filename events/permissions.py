# permissions.py
from rest_framework.permissions import BasePermission

class IsEventOwnerRole(BasePermission):

    message = "Only event owners can perform this action."

    def has_permission(self, request, view):

        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == request.user.Role.OWNER
        )
    