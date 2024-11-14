from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Разрешение позволяет доступ только владельцу объекта.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
