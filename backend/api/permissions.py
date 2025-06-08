from rest_framework import permissions


class IsOwnOrReadOnly(permissions.BasePermission):
    """
    Позволяет изменять или удалять контент только его авторам.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
