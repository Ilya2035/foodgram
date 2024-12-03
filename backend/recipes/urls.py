from django.urls import path
from .views import RecipeListCreateView, RecipeDetailView

urlpatterns = [
    path('api/recipes/', RecipeListCreateView.as_view(), name='recipe-list-create'),
    path('api/recipes/<int:id>/', RecipeDetailView.as_view(), name='recipe-detail'),
]
