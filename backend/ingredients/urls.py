from django.urls import path
from .views import IngredientListView, IngredientDetailView

urlpatterns = [
    path('api/ingredients/', IngredientListView.as_view(), name='ingredient-list'),
    path('api/ingredients/<int:pk>/', IngredientDetailView.as_view(), name='ingredient-detail'),
]
