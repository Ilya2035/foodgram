"""
Основные маршруты проекта Foodgram.

Этот модуль определяет маршруты для всех приложений проекта.
"""

from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('tags.urls')),
    path('', include('ingredients.urls')),
    path('', include('recipes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
