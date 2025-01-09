"""
Сериализаторы для моделей Ingredient, User, Tag и Recipe.

Этот модуль предоставляет сериализаторы для работы с моделями Ingredient, User,
Tag и Recipe, включая их обработку, валидацию данных и преобразование.
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

# Внутренние импорты
from recipes.fields import Base64ImageField
from recipes.models import (
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart
)
from tags.models import Tag
from ingredients.models import Ingredient
from users.models import Profile, Subscription

class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Ingredient.

    Преобразует данные ингредиента для API.
    """

    class Meta:
        """
        Метаданные для сериализатора Ingredient.

        Указывает модель и поля, которые будут включены в сериализацию.
        """

        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']

##############################################################################

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

##############################################################################

class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag.

    Используется для представления данных тега в формате JSON.
    """

    class Meta:
        """
        Метаданные для TagSerializer.

        Определяет модель Tag и поля для сериализации.
        """

        model = Tag
        fields = ['id', 'name', 'slug']

#############################################################################

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания пользователя.

    Включает проверку уникальности username и email,
    а также проверку пароля.
    """

    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        required=True,
        max_length=128,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message="Никнейм может содержать"
                        " только буквы, цифры и символы @ . + - _"
            )
        ]
    )
    first_name = serializers.CharField(required=True, max_length=128)
    last_name = serializers.CharField(required=True, max_length=128)

    class Meta:
        """
        Метаданные для UserCreateSerializer.

        Указывает модель User и поля для сериализации.
        """

        model = User
        fields = ['id', 'email', 'username',
                  'first_name', 'last_name', 'password']

    def validate_email(self, value):
        """Проверяем, что email уникален."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует.")
        return value

    def validate_username(self, value):
        """Проверяем, что username уникален."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким username уже существует.")
        return value

    def validate(self, attrs):
        """Вызов встроенной проверки пароля."""
        password = attrs.get('password')
        user = User(
            username=attrs.get('username'),
            email=attrs.get('email'),
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', '')
        )
        try:
            validate_password(password, user=user)
        except ValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        """Создаёт пользователя и профиль."""
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        Profile.objects.get_or_create(user=user)
        return user


class UserListRetrieveSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения пользователя.

    Включает поля is_subscribed и avatar.
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        """
        Метаданные для UserListRetrieveSerializer.

        Указывает модель User и поля для сериализации.
        """

        model = User
        fields = [
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на obj."""
        request = self.context.get('request')
        user = request.user
        if not user.is_authenticated:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя, если он существует."""
        request = self.context.get('request')
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return request.build_absolute_uri(obj.profile.avatar.url)
        return None


class SetPasswordSerializer(serializers.Serializer):
    """
    Сериализатор для изменения пароля пользователя.

    Включает поля current_password и new_password.
    """

    new_password = serializers.CharField()
    current_password = serializers.CharField()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        """
        Метаданные для AvatarSerializer.

        Указывает модель Profile и поле avatar.
        """

        model = Profile
        fields = ['avatar']


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """
    Упрощённый сериализатор для рецептов.

    Отображает только основные поля.
    """

    class Meta:
        """
        Метаданные для RecipeMinifiedSerializer.

        Указывает модель Recipe и поля для сериализации.
        """

        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class UserWithRecipesSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения пользователя с его рецептами.

    Включает поля is_subscribed, recipes, recipes_count и avatar.
    """

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        """
        Метаданные для UserWithRecipesSerializer.

        Указывает модель User и поля для сериализации.
        """

        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на obj."""
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False

    def get_recipes(self, obj):
        """Возвращает список рецептов автора с учетом лимита."""
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Возвращает количество рецептов автора."""
        return Recipe.objects.filter(author=obj).count()

    def get_avatar(self, obj):
        """Возвращает URL аватара пользователя, если он существует."""
        request = self.context.get('request')
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return request.build_absolute_uri(obj.profile.avatar.url)
        return None
