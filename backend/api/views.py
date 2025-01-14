from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet

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
    FoodgramUserSerializer,
    UserBriefSerializer, FavoriteSerializer, ShoppingCartSerializer
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

        is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        if is_in_shopping_cart == '1' and user.is_authenticated:
            qs = qs.filter(
                Exists(
                    ShoppingCart.objects.filter(user=user, recipe=OuterRef('id'))
                )
            )
        elif is_in_shopping_cart == '0' and user.is_authenticated:
            qs = qs.exclude(
                Exists(
                    ShoppingCart.objects.filter(user=user, recipe=OuterRef('id'))
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
        # Предполагается, что short_link всегда присутствует
        short_link = request.build_absolute_uri(f"/s/{recipe.short_link}/")
        return Response(
            {"short-link": short_link}, status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок — агрегируем ингредиенты одним запросом."""
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
                unit=F('recipe__recipe_ingredients__ingredient__measurement_unit'),
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
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавляет или удаляет рецепт из избранного."""
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
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
        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Рецепта нет в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет или удаляет рецепт из списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == 'POST':
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
        elif request.method == 'DELETE':
            cart_item = ShoppingCart.objects.filter(user=request.user, recipe=recipe)
            if cart_item.exists():
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Рецепта нет в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST
            )


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
        if request.method == 'GET':
            return super().me(request, *args, **kwargs)
        return Response(
            {'detail': 'Method not allowed.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Подписка/отписка на пользователя."""
        author = self.get_object()
        user = request.user

        if user == author:
            return Response(
                {"detail": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                user=user, author=author)
            if not created:
                return Response(
                    {"detail": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UserWithRecipesSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            subscription = Subscription.objects.filter(
                user=user, author=author)
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"detail": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение списка подписок текущего пользователя."""
        user = request.user
        subscriptions = Subscription.objects.filter(
            user=user).select_related('author')

        # Пагинация
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                [subscription.author for subscription in page],
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            [subscription.author for subscription in subscriptions],
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def avatar(self, request):
        """Обновление или удаление аватара пользователя."""
        user = request.user

        if request.method == 'PUT':
            serializer = AvatarSerializer(instance=user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            avatar_url = request.build_absolute_uri(
                user.avatar.url) if user.avatar else None
            return Response({'avatar': avatar_url},
                            status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save(update_fields=['avatar'])
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(
                {"detail": "Аватар не установлен."},
                status=status.HTTP_400_BAD_REQUEST
            )
