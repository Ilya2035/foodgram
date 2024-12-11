from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Recipe, RecipeIngredient, Favorite, ShoppingCart
from ingredients.models import Ingredient
from tags.models import Tag
from .fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(required=True, source='recipe_ingredients', many=True)
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    author = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        ]

    def validate(self, data):
        # Проверка на пустые или некорректные поля
        ingredients = data.get('recipe_ingredients', [])
        if not ingredients:
            raise serializers.ValidationError({'ingredients': 'Это поле не может быть пустым.'})

        unique_ingredients = set()
        for ingredient in ingredients:
            ingredient_id = ingredient.get('ingredient').id
            if ingredient_id in unique_ingredients:
                raise serializers.ValidationError({'ingredients': 'Ингредиенты не должны повторяться.'})
            unique_ingredients.add(ingredient_id)

            amount = ingredient.get('amount')
            if amount is None or int(amount) < 1:
                raise serializers.ValidationError({'ingredients': 'Количество каждого ингредиента должно быть не менее 1.'})

        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError({'tags': 'Это поле не может быть пустым.'})

        return data

    def get_author(self, obj):
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
        user = self.context['request'].user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients')
        tags_data = validated_data.pop('tags', [])

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredients', None)
        tags_data = validated_data.pop('tags', [])

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

        instance.tags.set(tags_data)
        instance.save()
        return instance


class RecipeSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']
