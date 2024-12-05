import urllib.parse

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework import permissions

from .models import Ingredient
from .serializers import IngredientSerializer


class IngredientListView(ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = []
    search_fields = []
    search_param = 'name'

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', '')
        name = urllib.parse.unquote(name)
        print(f"Декодированный параметр name: {name}")
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class IngredientDetailView(RetrieveAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
