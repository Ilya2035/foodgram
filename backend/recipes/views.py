from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, filters
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView
)
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .filters import RecipeFilter
from .models import Recipe, ShoppingCart, Favorite
from .serializers import RecipeSerializer, RecipeSimpleSerializer
from .pagination import PaginationforUser


class RecipeListCreateView(ListCreateAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PaginationforUser
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ['name', 'text']

    def get_queryset(self):
        """Фильтрация рецептов по параметрам is_favorited и is_in_shopping_cart."""
        queryset = Recipe.objects.all()
        user = self.request.user

        # Фильтрация по избранному
        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1' and user.is_authenticated:
            queryset = queryset.filter(
                Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('id'))
                )
            )

        # Фильтрация по корзине покупок
        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart == '1' and user.is_authenticated:
            queryset = queryset.filter(
                Exists(
                    ShoppingCart.objects.filter(user=user, recipe=OuterRef('id'))
                )
            )
        elif is_in_shopping_cart == '0' and user.is_authenticated:
            queryset = queryset.exclude(
                Exists(
                    ShoppingCart.objects.filter(user=user, recipe=OuterRef('id'))
                )
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def patch(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            raise PermissionDenied({"detail": "У вас недостаточно прав для изменения данного рецепта."})
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            raise PermissionDenied({"detail": "У вас недостаточно прав для удаления данного рецепта."})
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeLinkView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        # Генерация короткой ссылки (пример, замените на реальную логику)
        short_link = f"https://foodgram.example.org/s/{recipe.id}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)


class DownloadShoppingCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user).select_related('recipe').prefetch_related('recipe__recipe_ingredients__ingredient')

        if not shopping_cart.exists():
            return Response({"detail": "Список покупок пуст."}, status=status.HTTP_400_BAD_REQUEST)

        # Формирование контента файла
        content = "Список покупок:\n\n"
        for item in shopping_cart:
            recipe = item.recipe
            content += f"{recipe.name}:\n"
            # Используем промежуточную модель RecipeIngredient для получения количества
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                amount = recipe_ingredient.amount
                content += f" - {ingredient.name} ({ingredient.measurement_unit}): {amount}\n"
            content += "\n"

        # Создание HTTP-ответа с файлом
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response


class ShoppingCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        """Добавление рецепта в список покупок."""
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({"detail": "Рецепт не найден."}, status=status.HTTP_404_NOT_FOUND)

        if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response({"detail": "Рецепт уже в списке покупок."}, status=status.HTTP_400_BAD_REQUEST)

        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeSimpleSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Удаление рецепта из списка покупок."""
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({"detail": "Рецепт не найден."}, status=status.HTTP_404_NOT_FOUND)

        try:
            shopping_cart_item = ShoppingCart.objects.get(user=request.user, recipe=recipe)
            shopping_cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ShoppingCart.DoesNotExist:
            return Response({"detail": "Рецепта нет в списке покупок."}, status=status.HTTP_400_BAD_REQUEST)


class FavoriteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        """Добавление рецепта в избранное."""
        recipe = get_object_or_404(Recipe, id=id)

        # Проверка: рецепт уже в избранном
        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response({"detail": "Рецепт уже в избранном."}, status=status.HTTP_400_BAD_REQUEST)

        # Добавление в избранное
        Favorite.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeSimpleSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Удаление рецепта из избранного."""
        recipe = get_object_or_404(Recipe, id=id)

        # Проверка: рецепт отсутствует в избранном
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe).first()
        if not favorite:
            return Response({"detail": "Рецепт отсутствует в избранном."}, status=status.HTTP_400_BAD_REQUEST)

        # Удаление из избранного
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
