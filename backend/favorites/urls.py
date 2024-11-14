from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import FavoriteViewSet

router = DefaultRouter()
router.register('favorites', FavoriteViewSet, basename='favorites')

urlpatterns = [
    path('', include(router.urls)),
]
