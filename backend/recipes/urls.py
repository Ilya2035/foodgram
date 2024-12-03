from django.urls import path
from .views import (
    RecipeListCreateView,
    RecipeDetailView,
    RecipeLinkView,
    DownloadShoppingCartView,
    ShoppingCartView
)

urlpatterns = [
    path('api/recipes/', RecipeListCreateView.as_view(), name='recipe-list-create'),
    path('api/recipes/<int:id>/', RecipeDetailView.as_view(), name='recipe-detail'),
    path('api/recipes/<int:id>/get-link/', RecipeLinkView.as_view(), name='recipe-get-link'),
    path('api/recipes/download_shopping_cart/', DownloadShoppingCartView.as_view(), name='download-shopping-cart'),
    path('api/recipes/<int:id>/shopping_cart/', ShoppingCartView.as_view(), name='shopping-cart')
]
