from django.urls import include, path
from rest_framework.routers import DefaultRouter


from .views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    FoodgramUserViewSet,
    ShortLinkRedirect,
)

v1_router = DefaultRouter()
v1_router.register('ingredients',
                   IngredientViewSet,
                   basename='ingredients')
v1_router.register('recipes',
                   RecipeViewSet,
                   basename='recipes')
v1_router.register('tags',
                   TagViewSet,
                   basename='tags')
v1_router.register('users',
                   FoodgramUserViewSet,
                   basename='users')

urlpatterns = [
    path('', include(v1_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls')),
    path('<str:short_link>/',
         ShortLinkRedirect.as_view(),
         name='recipes-short'),
]
