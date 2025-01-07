"""
URL-маршруты для приложения Tags.

Этот модуль определяет маршруты для работы с тегами через API.
"""

from django.urls import path
from .views import TagListView, TagDetailView

urlpatterns = [
    path(
        'api/tags/',
        TagListView.as_view(),
        name='tag-list'
    ),
    path(
        'api/tags/<int:pk>/',
        TagDetailView.as_view(),
        name='tag-detail'
    ),
]
