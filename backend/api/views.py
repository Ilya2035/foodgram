from djoser.views import UserViewSet as DjoserUserViewSet

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Exists, OuterRef, F, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.decorators import action
from rest_framework.response import Response

from .permissions import IsAuthorOrReadOnly
from .pagination import PaginationForUser
from .filters import RecipeFilter, IngredientFilter
from .serializers import (
    RecipeReadSerializer,
    RecipeWriteSerializer,
    IngredientSerializer,
    TagSerializer,
    AvatarSerializer,
    UserWithRecipesSerializer,
    UserBriefSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer
)
from ingredients.models import Ingredient
from recipes.models import Recipe, ShoppingCart, Favorite
from tags.models import Tag
from users.models import FoodgramUser, Subscription

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для списка и детального просмотра ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


def short_link_redirect(request, short_name):
    """
    По значению short_link (short_name) находим рецепт
    и делаем редирект на стандартный детальный URL.
    """
    recipe = get_object_or_404(Recipe, short_link=short_name)
    detail_url = reverse('recipes-detail', args=[recipe.pk])
    return redirect(detail_url)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PaginationForUser

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от действия."""
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        """Возвращает отфильтрованный queryset в зависимости от запроса."""
        qs = super().get_queryset()
        user = self.request.user

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1' and user.is_authenticated:
            qs = qs.filter(
                Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('id'))
                )
            )

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        if is_in_shopping_cart == '1' and user.is_authenticated:
            qs = qs.filter(
                Exists(
                    ShoppingCart.objects.filter(user=user, recipe=OuterRef(
                        'id'))
                )
            )
        elif is_in_shopping_cart == '0' and user.is_authenticated:
            qs = qs.exclude(
                Exists(
                    ShoppingCart.objects.filter(user=user, recipe=OuterRef(
                        'id'))
                )
            )

        return qs

    def perform_create(self, serializer):
        """Сохраняет рецепт с текущим пользователем как автором."""
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            f"/recipes/{recipe.short_link}/")
        return Response({"short-link": short_link},
                        status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок — агрегируем ингредиенты запросом."""
        user = request.user
        if not ShoppingCart.objects.filter(user=user).exists():
            return Response(
                {"detail": "Список покупок пуст."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients_qs = (
            ShoppingCart.objects
            .filter(user=user)
            .values(
                name=F('recipe__recipe_ingredients__ingredient__name'),
                unit=F(
                    'recipe__recipe_ingredients__ingredient__measurement_unit'
                ),
            )
            .annotate(total_amount=Sum('recipe__recipe_ingredients__amount'))
            .order_by('name')
        )

        lines = ["Список покупок:\n\n"]
        for item in ingredients_qs:
            lines.append(
                f"{item['name']} "
                f"({item['unit']}): "
                f"{item['total_amount']}\n"
            )

        content = "".join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def add_favorite(self, request, pk=None):
        """Добавляет рецепт в избранное."""
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @add_favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        """Удаляет рецепт из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if not deleted_count:
            return Response(
                {"detail": "Рецепта нет в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart'
    )
    def add_to_shopping_cart(self, request, pk=None):
        """Добавляет рецепт в список покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = ShoppingCartSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @add_to_shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk=None):
        """Удаляет рецепт из списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if not deleted_count:
            return Response(
                {"detail": "Рецепта нет в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов (list, retrieve)."""

    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class FoodgramUserViewSet(DjoserUserViewSet):
    """Кастомный UserViewSet на базе Djoser."""

    queryset = FoodgramUser.objects.all()
    serializer_class = UserBriefSerializer
    pagination_class = PaginationForUser

    def get_permissions(self):
        """Определяет права доступа в зависимости от действия."""
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от действия."""
        if self.action in ('list', 'retrieve', 'me'):
            return UserBriefSerializer
        return super().get_serializer_class()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        """Ограничивает методы эндпоинта me."""
        return super().me(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписка на пользователя."""
        author = self.get_object()
        serializer = SubscriptionSerializer(
            data={'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Отписка от пользователя."""
        author = self.get_object()
        user = request.user
        deleted_count, _ = Subscription.objects.filter(
            user=user, author=author
        ).delete()
        if not deleted_count:
            return Response(
                {"detail": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        user = request.user
        subscriptions = Subscription.objects.filter(user=user).select_related(
            'author')
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            authors = [subscription.author for subscription in page]
            serializer = UserWithRecipesSerializer(
                authors,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        authors = [subscription.author for subscription in subscriptions]
        serializer = UserWithRecipesSerializer(
            authors,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar_update(self, request):
        """Обновление аватара пользователя."""
        user = request.user
        serializer = AvatarSerializer(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        avatar_url = request.build_absolute_uri(
            user.avatar.url) if user.avatar else None
        return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

    @avatar_update.mapping.delete
    def avatar_delete(self, request):
        """Удаление аватара пользователя."""
        user = request.user
        if not user.avatar:
            return Response(
                {"detail": "Аватар не установлен."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.avatar.delete(
            save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
