from rest_framework.permissions import (SAFE_METHODS, BasePermission,
                                        IsAuthenticated)

from user.models import ADMIN


class IsOwnerAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
            or request.user.role == ADMIN
            or request.user.is_superuser
        )


class IsAuthenticatedCustom(IsAuthenticated):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj == request.user
