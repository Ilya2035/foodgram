from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

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
        return bool(
            request and user.is_authenticated and Subscription.objects.filter(
                user=user, author=obj).exists()
        )

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

    @staticmethod
    def create_ingredients(recipe, ingredients_data):
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
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
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


class AvatarSerializer(serializers.ModelSerializer):
    """Изменение аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        """Мета класс для AvatarSerializer."""

        model = FoodgramUser
        fields = ('avatar',)


class UserWithRecipesSerializer(UserBriefSerializer):
    """Сериализатор пользователя с его рецептами."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserBriefSerializer.Meta):
        """Мета класс для UserWithRecipesSerializer."""

        fields = UserBriefSerializer.Meta.fields + (
            'recipes', 'recipes_count',
        )

    def get_recipes(self, obj):
        """Возвращает рецепты пользователя с ограничением по количеству."""
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
        """Возвращает общее количество рецептов пользователя."""
        return Recipe.objects.filter(author=obj).count()


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Favorite."""

    class Meta:
        """Метаданные для серилизатора."""

        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe'],
                message="Рецепт уже в избранном."
            )
        ]

    def validate(self, attrs):
        """Валидатор для мерилизатора."""
        user = attrs.get('user')
        recipe = attrs.get('recipe')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже в избранном.")
        return attrs

    def to_representation(self, instance):
        """Возвращает данные через `RecipeSimpleSerializer`."""
        return RecipeSimpleSerializer(
            instance.recipe, context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для модели ShoppingCart."""

    class Meta:
        """Метаданные для серилизатора."""

        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=['user', 'recipe'],
                message="Рецепт уже в списке покупок."
            )
        ]

    def validate(self, attrs):
        """Валидатор для мерилизатора."""
        user = attrs.get('user')
        recipe = attrs.get('recipe')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже в списке покупок.")
        return attrs

    def to_representation(self, instance):
        """Возвращает данные через `RecipeSimpleSerializer`."""
        return RecipeSimpleSerializer(
            instance.recipe, context=self.context).data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Серидлизатор для логики подписок."""

    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=FoodgramUser.objects.all()
    )

    class Meta:
        """Метаданные для серилизатора."""

        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        """
        Проверяет, что пользователь не подписывается на себя.

        и подписка ещё не существует.
        """
        user = data.get('user')
        author = data.get('author')

        if user == author:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя.")

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя.")

        return data

    def to_representation(self, instance):
        """Возвращает данные автора через `UserWithRecipesSerializer."""
        return UserWithRecipesSerializer(
            instance.author,
            context={'request': self.context.get('request')}
        ).data
