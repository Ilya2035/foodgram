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
    path('', include('api.api_ingredients.urls')),
    path('', include('api.api_recipes.urls')),
    path('', include('api.api_tags.urls')),
    path('', include('api.api_users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
