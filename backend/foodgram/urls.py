from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Админка Django
    path('admin/', admin.site.urls),

    # Аутентификация (используя Djoser)
    path('api/auth/', include('djoser.urls')),  # Основные URL Djoser
    path('api/auth/', include('djoser.urls.jwt')),  # JWT-эндпоинты Djoser

    # Маршруты приложения users
    path('api/users/', include('users.urls')),

    # Маршруты приложения recipes
    path('api/recipes/', include('recipes.urls')),

    # Маршруты приложения ingredients
    path('api/ingredients/', include('ingredients.urls')),

    # Маршруты приложения tags
    path('api/tags/', include('tags.urls')),

    # Маршруты приложения favorites
    path('api/favorites/', include('favorites.urls')),

    # Маршруты приложения list (список покупок)
    path('api/list/', include('list.urls')),

    # Маршруты приложения subscriptions
    path('api/subscriptions/', include('subscriptions.urls')),

    # Маршруты приложения static_pages (если есть статические страницы)
    # path('', include('static_pages.urls')),
]

# Настройка для обработки медиафайлов в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
