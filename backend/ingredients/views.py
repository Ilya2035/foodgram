"""
Представления для приложения Ingredients.

Этот модуль содержит API-представления для работы с ингредиентами.
"""

import urllib.parse

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework import permissions

from .models import Ingredient
from .serializers import IngredientSerializer


class IngredientListView(ListAPIView):
    """Представление для получения списка ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = []
    search_fields = []
    search_param = 'name'
    pagination_class = None

    def get_queryset(self):
        """Возвращает отфильтрованный список ингредиентов."""
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', '')
        name = urllib.parse.unquote(name)
        print(f"Декодированный параметр name: {name}")
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class IngredientDetailView(RetrieveAPIView):
    """Представление для получения информации об отдельном ингредиенте."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
