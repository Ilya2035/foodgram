from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .fields import Base64ImageField
from recipes.models import Recipe, RecipeIngredient, Favorite, ShoppingCart
from tags.models import Tag
from ingredients.models import Ingredient
from users.models import FoodgramUser, Subscription


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class UserBriefSerializer(serializers.ModelSerializer):
    """Краткая информация о пользователе."""

    class Meta:
        model = FoodgramUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name')


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Чтение ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
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
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        return bool(
            user and user.is_authenticated and
            Favorite.objects.filter(user=user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        return bool(
            user and user.is_authenticated and
            ShoppingCart.objects.filter(user=user, recipe=obj).exists()
        )


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
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients',
            'name', 'image', 'text', 'cooking_time'
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    def validate(self, attrs):
        tags = attrs.get('tags', [])
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({
                'tags': 'Теги не должны повторяться.'
            })

        ings = attrs.get('recipe_ingredients', [])
        ing_ids = [item['ingredient'].id for item in ings]
        if len(ing_ids) != len(set(ing_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться.'
            })

        return attrs

    def create_ingredients(self, recipe, ingredients_data):
        bulk_list = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(bulk_list)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ings = validated_data.pop('recipe_ingredients', [])
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ings)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ings = validated_data.pop('recipe_ingredients', None)
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)
        if ings is not None:
            instance.recipe_ingredients.all().delete()
            self.create_ingredients(instance, ings)
        return instance

class RecipeSimpleSerializer(serializers.ModelSerializer):
    """Минимальный набор полей рецепта."""
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

class UserListRetrieveSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(user=request.user, author=obj).exists()
        return False

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class AvatarSerializer(serializers.ModelSerializer):
    """Изменение аватара пользователя."""
    avatar = Base64ImageField()

    class Meta:
        model = FoodgramUser
        fields = ('avatar',)


class UserWithRecipesSerializer(UserListRetrieveSerializer):
    """Сериализатор пользователя с рецептами."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserListRetrieveSerializer.Meta):
        fields = UserListRetrieveSerializer.Meta.fields + (
            'recipes', 'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            try:
                limit = int(recipes_limit)
                recipes = recipes[:limit]
            except ValueError:
                pass
        return RecipeSimpleSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения аватара пользователя."""
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = FoodgramUser
        fields = ('avatar',)


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, attrs):
        user = attrs['user']
        author = attrs['author']
        if user == author:
            raise serializers.ValidationError("Нельзя подписаться на самого себя.")
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError("Вы уже подписаны на этого пользователя.")
        return attrs

class FoodgramUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""
    password = serializers.CharField(write_only=True, required=True)
    re_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = FoodgramUser
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
            're_password',
        )

    def validate_password(self, value):
        """Валидирует пароль."""
        validate_password(value)
        return value

    def validate(self, attrs):
        """Проверяет совпадение паролей."""
        password = attrs.get('password')
        re_password = attrs.pop('re_password', None)

        if re_password and password != re_password:
            raise serializers.ValidationError({"re_password": "Пароли не совпадают."})

        return attrs

    def create(self, validated_data):
        """Создаёт пользователя и профиль."""
        re_password = validated_data.pop('re_password', None)
        user = FoodgramUser.objects.create_user(**validated_data)
        return user
