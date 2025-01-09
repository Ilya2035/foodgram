"""
URL-маршруты для API.

Этот модуль содержит маршруты для работы с различными приложениями API:
- Ingredients: маршруты для работы с ингредиентами.
- Recipes: маршруты для работы с рецептами.
- Tags: маршруты для работы с тегами.
- Users: маршруты для работы с пользователями, включая авторизацию,
  управление профилем и подписки.
"""

from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    CurrentUserView,
    ChangePasswordView,
    UserListView,
    UserDetailView,
    UpdateAvatarView,
    SubscriptionsView,
    SubscribeView,
    TagListView,
    TagDetailView,
    RecipeListCreateView,
    RecipeDetailView,
    RecipeLinkView,
    DownloadShoppingCartView,
    ShoppingCartView,
    FavoriteView,
    IngredientListView,
    IngredientDetailView
)

urlpatterns = [
    # Ingredients
    path(
        'api/ingredients/',
        IngredientListView.as_view(),
        name='ingredient-list'
    ),
    path(
        'api/ingredients/<int:pk>/',
        IngredientDetailView.as_view(),
        name='ingredient-detail'
    ),

    # Recipes
    path(
        'api/recipes/',
        RecipeListCreateView.as_view(),
        name='recipe-list-create'
    ),
    path(
        'api/recipes/download_shopping_cart/',
        DownloadShoppingCartView.as_view(),
        name='download-shopping-cart'
    ),
    path(
        'api/recipes/<int:pk>/',
        RecipeDetailView.as_view(),
        name='recipe-detail'
    ),
    path(
        'api/recipes/<int:id>/get-link/',
        RecipeLinkView.as_view(),
        name='recipe-get-link'
    ),
    path(
        'api/recipes/<int:id>/shopping_cart/',
        ShoppingCartView.as_view(),
        name='shopping-cart'
    ),
    path(
        'api/recipes/<int:id>/favorite/',
        FavoriteView.as_view(),
        name='favorite'
    ),

    # Tags
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

    # Users
    path(
        'api/auth/token/login/',
        LoginView.as_view(),
        name='login'
    ),
    path(
        'api/auth/token/logout/',
        LogoutView.as_view(),
        name='token-logout'
    ),
    path(
        'api/users/',
        UserListView.as_view(),
        name='user-list'
    ),
    path(
        'api/users/<int:id>/',
        UserDetailView.as_view(),
        name='user-detail'
    ),
    path(
        'api/users/me/',
        CurrentUserView.as_view(),
        name='current-user'
    ),
    path(
        'api/users/me/avatar/',
        UpdateAvatarView.as_view(),
        name='update-avatar'
    ),
    path(
        'api/users/set_password/',
        ChangePasswordView.as_view(),
        name='set-password'
    ),
    path(
        'api/users/subscriptions/',
        SubscriptionsView.as_view(),
        name='subscriptions'
    ),
    path(
        'api/users/<int:id>/subscribe/',
        SubscribeView.as_view(),
        name='subscribe'
    ),
]
