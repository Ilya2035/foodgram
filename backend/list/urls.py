from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ShoppingListViewSet

router = DefaultRouter()
router.register('list', ShoppingListViewSet, basename='list')

urlpatterns = [
    path('', include(router.urls)),
]
