from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, filters
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
    GenericAPIView
)
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .filters import RecipeFilter
from .models import Recipe, ShoppingCart, Favorite
from .serializers import RecipeSerializer, RecipeSimpleSerializer
from .pagination import PaginationforUser


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение: для SAFE-методов доступ открыт всем,
    для небезопасных методов — только автору объекта.
    """
    message = "У вас недостаточно прав для выполнения данного действия."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class RecipeListCreateView(ListCreateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PaginationforUser
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ['name', 'text']

    def get_queryset(self):
        """Фильтрация рецептов по параметрам is_favorited и is_in_shopping_cart."""
        queryset = super().get_queryset()
        user = self.request.user

        # Фильтрация по избранному
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1' and user.is_authenticated:
            queryset = queryset.filter(
                Exists(Favorite.objects.filter(user=user, recipe=OuterRef('id')))
            )

        # Фильтрация по корзине покупок
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart == '1' and user.is_authenticated:
            queryset = queryset.filter(
                Exists(ShoppingCart.objects.filter(user=user, recipe=OuterRef('id')))
            )
        elif is_in_shopping_cart == '0' and user.is_authenticated:
            queryset = queryset.exclude(
                Exists(ShoppingCart.objects.filter(user=user, recipe=OuterRef('id')))
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class RecipeLinkView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        short_link = f"https://foodgram.example.org/s/{recipe.id}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)


class DownloadShoppingCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(
            user=user
        ).select_related('recipe').prefetch_related('recipe__recipe_ingredients__ingredient')

        if not shopping_cart.exists():
            return Response({"detail": "Список покупок пуст."}, status=status.HTTP_400_BAD_REQUEST)

        lines = ["Список покупок:\n\n"]
        for item in shopping_cart:
            recipe = item.recipe
            lines.append(f"{recipe.name}:\n")
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                lines.append(f" - {ingredient.name} ({ingredient.measurement_unit}): {recipe_ingredient.amount}\n")
            lines.append("\n")

        content = "".join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response


class BaseRecipeRelationView(APIView):
    """
    Базовый класс для добавления/удаления рецептов в списки (избранное, корзина).
    Дочерние классы переопределяют relation_model, already_exists_error и not_exists_error.
    """
    permission_classes = [permissions.IsAuthenticated]
    relation_model = None
    already_exists_error = ""
    not_exists_error = ""

    def get_recipe(self):
        return get_object_or_404(Recipe, id=self.kwargs.get('id'))

    def post(self, request, id):
        recipe = self.get_recipe()
        if self.relation_model.objects.filter(user=request.user, recipe=recipe).exists():
            return Response({"detail": self.already_exists_error}, status=status.HTTP_400_BAD_REQUEST)

        self.relation_model.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeSimpleSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = self.get_recipe()
        relation_item = self.relation_model.objects.filter(user=request.user, recipe=recipe).first()
        if not relation_item:
            return Response({"detail": self.not_exists_error}, status=status.HTTP_400_BAD_REQUEST)
        relation_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(BaseRecipeRelationView):
    relation_model = ShoppingCart
    already_exists_error = "Рецепт уже в списке покупок."
    not_exists_error = "Рецепта нет в списке покупок."


class FavoriteView(BaseRecipeRelationView):
    relation_model = Favorite
    already_exists_error = "Рецепт уже в избранном."
    not_exists_error = "Рецепт отсутствует в избранном."