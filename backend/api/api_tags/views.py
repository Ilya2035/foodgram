"""
Views для приложения Tags.

Этот модуль содержит представления для работы с тегами.
"""

from rest_framework import permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView

from tags.models import Tag
from .serializers import TagSerializer


class TagListView(ListAPIView):
    """
    Представление для отображения списка тегов.

    Доступно для всех пользователей.
    """

    permission_classes = [permissions.AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class TagDetailView(RetrieveAPIView):
    """
    Представление для отображения деталей тега.

    Доступно для всех пользователей.
    """

    permission_classes = [permissions.AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
