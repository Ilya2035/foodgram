"""
Сериализаторы для приложения Recipes.

Этот модуль содержит сериализаторы для работы с рецептами,
ингредиентами, тегами, избранным и списком покупок.
"""

from rest_framework import serializers

from recipes.models import (
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)
from ingredients.models import Ingredient
from tags.models import Tag
from recipes.fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag.

    Используется для отображения информации о тегах.
    """

    class Meta:
        """
        Метаданные для TagSerializer.

        Указывает модель и поля для сериализации.
        """

        model = Tag
        fields = ['id', 'name', 'slug']


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингредиентов в рецепте.

    Отображает информацию об ингредиентах, включая их количество.
    """

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        """
        Метаданные для IngredientInRecipeSerializer.

        Указывает модель RecipeIngredient и поля для сериализации.
        """

        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Recipe.

    Отображает информацию о рецепте, включая ингредиенты,
    теги, автора и статус избранного.
    """

    ingredients = IngredientInRecipeSerializer(
        required=True,
        source='recipe_ingredients',
        many=True
    )
    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """
        Метаданные для RecipeSerializer.

        Указывает модель Recipe и поля для сериализации.
        """

        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        ]

    def validate(self, data):
        """
        Проверяет данные рецепта на корректность.

        Проверка включает уникальность тегов и ингредиентов,
        а также валидность времени приготовления.
        """
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Это поле обязательно.'
            })

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({
                'tags': 'Теги не должны повторяться.'
            })

        nonexistent_tags = [
            tag_id for tag_id in tags
            if not Tag.objects.filter(id=tag_id).exists()
        ]
        if nonexistent_tags:
            raise serializers.ValidationError({
                'tags': (
                    f'Некоторые из указанных тегов не существуют: '
                    f'{nonexistent_tags}.'
                )
            })

        ingredients = data.get('recipe_ingredients', [])
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Это поле не может быть пустым.'
            })

        unique_ingredients = set()
        for ingredient in ingredients:
            ingredient_id = ingredient.get('ingredient').id
            if ingredient_id in unique_ingredients:
                raise serializers.ValidationError({
                    'ingredients': 'Ингредиенты не должны повторяться.'
                })
            unique_ingredients.add(ingredient_id)

            amount = ingredient.get('amount')
            if amount is None or int(amount) < 1:
                raise serializers.ValidationError({
                    'ingredients': (
                        'Количество каждого ингредиента'
                        ' должно быть не менее 1.'
                    )
                })

        cooking_time = data.get('cooking_time')
        if cooking_time is None or int(cooking_time) < 1:
            raise serializers.ValidationError({
                'cooking_time': (
                    'Время приготовления должно быть не менее 1 минуты.'
                )
            })

        return data

    def get_author(self, obj):
        """Возвращает информацию об авторе рецепта."""
        user = obj.author
        request = self.context.get('request')
        avatar_url = None
        if hasattr(user, 'profile') and user.profile.avatar:
            avatar_url = request.build_absolute_uri(user.profile.avatar.url)
        return {
            "email": user.email,
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "is_subscribed": False,
            "avatar": avatar_url
        }

    def get_is_favorited(self, obj):
        """Проверяет, находится ли рецепт в избранном у пользователя."""
        user = self.context['request'].user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в списке покупок у пользователя."""
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    def create(self, validated_data):
        """Создаёт новый рецепт с ингредиентами и тегами."""
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = self.initial_data.get('tags', [])

        recipe = Recipe.objects.create(**validated_data)
        if tags_data:
            recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт с ингредиентами и тегами."""
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        tags_data = self.initial_data.get('tags', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient_data['ingredient'],
                    amount=ingredient_data['amount']
                )

        if tags_data:
            instance.tags.set(tags_data)

        instance.save()
        return instance


class RecipeSimpleSerializer(serializers.ModelSerializer):
    """
    Сериализатор для упрощённого отображения рецепта.

    Отображает только основные поля: название, изображение и время.
    """

    class Meta:
        """
        Метаданные для RecipeSimpleSerializer.

        Указывает модель Recipe и поля для сериализации.
        """

        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']
