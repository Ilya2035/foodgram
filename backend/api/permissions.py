from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешает доступ только автору для небезопасных методов."""

    message = "У вас недостаточно прав для выполнения данного действия."

    def has_object_permission(self, request, view, obj):
        """Определяет права доступа для объекта."""
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
