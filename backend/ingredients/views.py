from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework import permissions
from django_filters.rest_framework import DjangoFilterBackend

from .models import Ingredient
from .serializers import IngredientSerializer
from .filters import IngredientFilter


class IngredientListView(ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class IngredientDetailView(RetrieveAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
