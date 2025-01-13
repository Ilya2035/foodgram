from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator

from .fields import Base64ImageField
from recipes.models import Recipe, RecipeIngredient, Favorite, ShoppingCart
from tags.models import Tag
from ingredients.models import Ingredient
from users.models import FoodgramUser, Subscription


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        """Мета класс для IngredientSerializer."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        """Мета класс для TagSerializer."""

        model = Tag
        fields = ('id', 'name', 'slug')


class UserBriefSerializer(serializers.ModelSerializer):
    """Краткая информация о пользователе."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        """Мета класс для UserBriefSerializer."""

        model = FoodgramUser
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного автора."""
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False

    def get_avatar(self, obj):
        """Возвращает URL аватара автора, если он есть."""
        request = self.context.get('request')
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Чтение ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        """Мета класс для IngredientInRecipeReadSerializer."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    """Запись ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        """Мета класс для IngredientInRecipeWriteSerializer."""

        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Чтение рецептов (list/retrieve)."""

    author = UserBriefSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeReadSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    image = Base64ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField()

    class Meta:
        """Мета класс для RecipeReadSerializer."""

        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное пользователем."""
        request = self.context.get('request')
        user = request.user if request else None
        return bool(user and user.is_authenticated and Favorite.objects.filter(
            user=user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в корзину покупок пользователем."""
        request = self.context.get('request')
        user = request.user if request else None
        return bool(
            user and user.is_authenticated and ShoppingCart.objects.filter(
                user=user, recipe=obj).exists())


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Создание и обновление рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientInRecipeWriteSerializer(
        source='recipe_ingredients',
        many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        """Мета класс для RecipeWriteSerializer."""

        model = Recipe
        fields = (
            'id', 'tags', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )

    def to_representation(self, instance):
        """Возвращает данные через `RecipeReadSerializer`."""
        return RecipeReadSerializer(instance, context=self.context).data

    def validate(self, attrs):
        """Валидация данных для создания/обновления рецепта."""
        tags = attrs.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Это поле не может быть пустым.'
            })

        ingredients = attrs.get('recipe_ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Это поле не может быть пустым.'
            })

        # Проверка уникальности тегов
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({
                'tags': 'Теги не должны повторяться.'
            })

        # Проверка уникальности ингредиентов
        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться.'
            })

        return attrs

    def create_ingredients(self, recipe, ingredients_data):
        """Создаёт связи между рецептом и ингредиентами."""
        bulk_list = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(bulk_list)

    def create(self, validated_data):
        """Создаёт рецепт с тегами и ингредиентами."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет рецепт, теги и ингредиенты."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('recipe_ingredients', None)
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(instance, ingredients)
        return instance


class RecipeSimpleSerializer(serializers.ModelSerializer):
    """Минимальный набор полей рецепта."""

    image = Base64ImageField(read_only=True)

    class Meta:
        """Мета класс для RecipeSimpleSerializer."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserListRetrieveSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        """Мета класс для UserListRetrieveSerializer."""

        model = FoodgramUser
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли пользователь на данного автора."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj).exists()
        return False

    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя, если он есть."""
        request = self.context.get('request')
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class AvatarSerializer(serializers.ModelSerializer):
    """Изменение аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        """Мета класс для AvatarSerializer."""

        model = FoodgramUser
        fields = ('avatar',)


class UserWithRecipesSerializer(UserListRetrieveSerializer):
    """Сериализатор пользователя с его рецептами."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserListRetrieveSerializer.Meta):
        """Мета класс для UserWithRecipesSerializer."""

        fields = UserListRetrieveSerializer.Meta.fields + (
            'recipes', 'recipes_count',
        )

    def get_recipes(self, obj):
        """Возвращает рецепты пользователя с ограничением по количеству."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        print(f"DEBUG: recipes_limit={recipes_limit}")
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            try:
                limit = int(recipes_limit)
                recipes = recipes[:limit]
            except ValueError:
                pass
        return RecipeSimpleSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов пользователя."""
        return Recipe.objects.filter(author=obj).count()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    class Meta:
        """Мета класс для SubscriptionCreateSerializer."""

        model = Subscription
        fields = ('user', 'author')

    def validate(self, attrs):
        """Валидирует создание подписки."""
        user = attrs['user']
        author = attrs['author']
        if user == author:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя.")
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя.")
        return attrs


class FoodgramUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""

    password = serializers.CharField(write_only=True, required=True)
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Никнейм может содержать'
                        ' только буквы, цифры и символы @ . + - _',
                code='invalid_username'
            ),
            UniqueValidator(
                queryset=FoodgramUser.objects.all(),
                message='Пользователь с таким никнеймом уже существует.'
            )
        ]
    )
    email = serializers.EmailField(
        max_length=254,
        required=True,
        validators=[
            UniqueValidator(
                queryset=FoodgramUser.objects.all(),
                message='Пользователь с таким email уже существует.'
            )
        ]
    )
    first_name = serializers.CharField(
        max_length=150,
        required=True
    )
    last_name = serializers.CharField(
        max_length=150,
        required=True
    )

    class Meta:
        """Мета класс для FoodgramUserCreateSerializer."""

        model = FoodgramUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_password(self, value):
        """Валидирует пароль."""
        validate_password(value)
        return value

    def create(self, validated_data):
        """Создаёт пользователя."""
        user = FoodgramUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user
