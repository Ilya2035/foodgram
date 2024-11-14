from rest_framework.permissions import BasePermission


class IsAuthenticatedAndNotAuthor(BasePermission):
    """
    Разрешение, которое позволяет только
    аутентифицированным пользователям,
    которые не являются автором.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user != view.get_object()
