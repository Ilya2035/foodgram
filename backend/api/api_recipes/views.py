"""
Views для приложения Recipes.

Этот модуль содержит представления для работы с рецептами,
списком покупок и избранным, включая создание, обновление и удаление.
"""

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
from django.shortcuts import get_object_or_404

from recipes.filters import RecipeFilter
from recipes.models import Recipe, ShoppingCart, Favorite
from .serializers import RecipeSerializer, RecipeSimpleSerializer
from recipes.pagination import PaginationforUser


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение: доступ для SAFE-методов открыт всем.

    Для небезопасных методов доступ предоставляется только автору объекта.
    """

    message = "У вас недостаточно прав для выполнения данного действия."

    def has_object_permission(self, request, view, obj):
        """
        Проверяет разрешения для объекта.

        Разрешает доступ для SAFE-методов или автору объекта.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class RecipeListCreateView(ListCreateAPIView):
    """
    Представление для отображения списка рецептов и создания нового.

    Поддерживает фильтрацию по избранному и корзине покупок.
    """

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = PaginationforUser
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ['name', 'text']

    def get_queryset(self):
        """
        Возвращает отфильтрованный список рецептов.

        Фильтрация по параметрам is_favorited и is_in_shopping_cart.
        """
        queryset = super().get_queryset()
        user = self.request.user

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1' and user.is_authenticated:
            queryset = queryset.filter(
                Exists(Favorite.objects.filter(
                    user=user,
                    recipe=OuterRef('id')))
            )

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart == '1' and user.is_authenticated:
            queryset = queryset.filter(
                Exists(ShoppingCart.objects.filter(
                    user=user, recipe=OuterRef('id')))
            )
        elif is_in_shopping_cart == '0' and user.is_authenticated:
            queryset = queryset.exclude(
                Exists(ShoppingCart.objects.filter(
                    user=user, recipe=OuterRef('id')))
            )

        return queryset

    def perform_create(self, serializer):
        """
        Создаёт рецепт с указанием автора.

        Автор берётся из текущего пользователя.
        """
        serializer.save(author=self.request.user)


class RecipeDetailView(RetrieveUpdateDestroyAPIView):
    """
    Представление для просмотра, обновления и удаления рецепта.

    Только автор рецепта имеет доступ к небезопасным методам.
    """

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsAuthorOrReadOnly]

    def get_serializer_context(self):
        """Добавляет объект запроса в контекст сериализатора."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class RecipeLinkView(APIView):
    """Представление для получения короткой ссылки на рецепт."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        """Возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, id=id)
        short_link = request.build_absolute_uri(recipe.get_absolute_url())
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)


class DownloadShoppingCartView(APIView):
    """
    Представление для скачивания списка покупок.

    Список формируется из рецептов, добавленных в корзину.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Возвращает текстовый файл со списком покупок."""
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(
            user=user
        ).select_related('recipe').prefetch_related(
            'recipe__recipe_ingredients__ingredient'
        )

        if not shopping_cart.exists():
            return Response(
                {"detail": "Список покупок пуст."},
                status=status.HTTP_400_BAD_REQUEST
            )

        lines = ["Список покупок:\n\n"]
        for item in shopping_cart:
            recipe = item.recipe
            lines.append(f"{recipe.name}: \n")
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                lines.append(
                    f" - {ingredient.name} ({ingredient.measurement_unit}): "
                    f"{recipe_ingredient.amount}\n"
                )
            lines.append("\n")

        content = "".join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = \
            'attachment; filename="shopping_cart.txt"'
        return response


class BaseRecipeRelationView(APIView):
    """
    Базовое представление для добавления/удаления рецептов в списки.

    Дочерние классы определяют модель связи и текст ошибок.
    """

    permission_classes = [permissions.IsAuthenticated]
    relation_model = None
    already_exists_error = ""
    not_exists_error = ""

    def get_recipe(self):
        """
        Возвращает рецепт по идентификатору.

        Вызывает 404 ошибку, если рецепт не найден.
        """
        return get_object_or_404(Recipe, id=self.kwargs.get('id'))

    def post(self, request, id):
        """
        Добавляет рецепт в список.

        Возвращает 400 ошибку, если рецепт уже в списке.
        """
        recipe = self.get_recipe()
        if self.relation_model.objects.filter(
                user=request.user, recipe=recipe).exists():
            return Response(
                {"detail": self.already_exists_error},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.relation_model.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeSimpleSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """
        Удаляет рецепт из списка.

        Возвращает 400 ошибку, если рецепт отсутствует в списке.
        """
        recipe = self.get_recipe()
        relation_item = self.relation_model.objects.filter(
            user=request.user, recipe=recipe
        ).first()
        if not relation_item:
            return Response(
                {"detail": self.not_exists_error},
                status=status.HTTP_400_BAD_REQUEST
            )
        relation_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(BaseRecipeRelationView):
    """Представление для управления списком покупок."""

    relation_model = ShoppingCart
    already_exists_error = "Рецепт уже в списке покупок."
    not_exists_error = "Рецепта нет в списке покупок."


class FavoriteView(BaseRecipeRelationView):
    """Представление для управления списком избранного."""

    relation_model = Favorite
    already_exists_error = "Рецепт уже в избранном."
    not_exists_error = "Рецепт отсутствует в избранном."
