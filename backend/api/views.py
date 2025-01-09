"""
Этот модуль содержит представления для работы с ингредиентами,
рецептами, тегами и пользователями.

Предоставляет API для создания, чтения, обновления и удаления объектов,
а также дополнительные функции, такие как фильтрация,
сортировка и управление связями.
"""

import urllib.parse

from django.db.models import Exists, OuterRef
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, filters
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
    ListAPIView,
    RetrieveAPIView
)
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from .serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeSerializer,
    RecipeSimpleSerializer,
    UserCreateSerializer,
    UserListRetrieveSerializer,
    SetPasswordSerializer,
    AvatarSerializer,
    UserWithRecipesSerializer,
)
from ingredients.models import Ingredient
from recipes.models import Recipe, ShoppingCart, Favorite
from tags.models import Tag
from users.models import Profile, Subscription
from recipes.filters import RecipeFilter
from recipes.pagination import PaginationforUser


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

##############################################################################

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

#############################################################################


class TagListView(ListAPIView):
    """
    Представление для отображения списка тегов.

    Доступно для всех пользователей.
    """

    permission_classes = [permissions.AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class TagDetailView(RetrieveAPIView):
    """
    Представление для отображения деталей тега.

    Доступно для всех пользователей.
    """

    permission_classes = [permissions.AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None

##############################################################################

class UserListView(ListCreateAPIView):
    """Представление для получения списка пользователей и создания нового."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = PaginationforUser

    def get_serializer_class(self):
        """Возвращает класс сериализатора в зависимости от метода запроса."""
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListRetrieveSerializer


class UserDetailView(RetrieveAPIView):
    """Представление для получения данных о конкретном пользователе."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserListRetrieveSerializer
    lookup_field = 'id'


class CurrentUserView(APIView):
    """Представление для получения данных о текущем авторизованном."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Возвращает данные о текущем пользователе."""
        serializer = UserListRetrieveSerializer(request.user,
                                                context={'request': request})
        return Response(serializer.data)


class UpdateAvatarView(APIView):
    """Представление для обновления или удаления аватара пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        """Обновляет аватар пользователя."""
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = AvatarSerializer(instance=profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            avatar_url = request.build_absolute_uri(profile.avatar.url)
            return Response({'avatar': avatar_url},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Удаляет аватар пользователя."""
        try:
            profile = request.user.profile
            if profile.avatar:
                profile.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Profile.DoesNotExist:
            return Response({"detail": "Профиль не найден."},
                            status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    """Представление для изменения пароля пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Изменяет пароль текущего пользователя."""
        serializer = SetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']
            user = request.user

            if not user.check_password(current_password):
                return Response(
                    {"current_password": ["Неверный текущий пароль."]},
                    status=status.HTTP_400_BAD_REQUEST)

            try:
                validate_password(new_password, user=user)
            except ValidationError as e:
                return Response(
                    {"new_password": list(e.messages)},
                    status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(ObtainAuthToken):
    """Представление для аутентификации пользователя и выдачи токена."""

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """Выполняет аутентификацию пользователя и возвращает токен."""
        email = request.data.get('email')
        password = request.data.get('password')
        if email is None or password is None:
            return Response(
                {"detail": "Необходимы email и password."},
                status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=email, password=password)
        if not user:
            user = User.objects.filter(email=email).first()
            if not user or not user.check_password(password):
                return Response(
                    {"detail": "Неверные учетные данные."},
                    status=status.HTTP_400_BAD_REQUEST)

        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


class LogoutView(APIView):
    """Представление для выхода пользователя и удаления токена."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Удаляет токен текущего пользователя."""
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
        except Token.DoesNotExist:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsView(ListAPIView):
    """Представление для получения списка подписок текущего пользователя."""

    serializer_class = UserWithRecipesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaginationforUser

    def get_queryset(self):
        """Возвращает пользователей, на которых подписан текущий."""
        return User.objects.filter(followers__user=self.request.user)


class SubscribeView(APIView):
    """Представление для подписки и отписки от пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        """Создаёт подписку текущего пользователя на указанного автора."""
        user = request.user
        author = get_object_or_404(User, id=id)

        if user == author:
            return Response({
                "detail": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST)

        if Subscription.objects.filter(user=user, author=author).exists():
            return Response({
                "detail": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST)

        Subscription.objects.create(user=user, author=author)
        serializer = UserWithRecipesSerializer(author,
                                               context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Удаляет подписку текущего пользователя на указанного автора."""
        user = request.user
        author = get_object_or_404(User, id=id)

        subscription = Subscription.objects.filter(user=user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"detail": "Вы не подписаны на этого пользователя."},
            status=status.HTTP_400_BAD_REQUEST)
