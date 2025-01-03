"""
Сериализаторы для приложения Users.

Этот модуль содержит сериализаторы для работы с пользователями,
их профилями, подписками и аватарами.
"""

import base64
import uuid
import imghdr

from django.core.files.base import ContentFile
from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Profile, Subscription
from recipes.models import Recipe


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
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar']

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на obj."""
        user = self.context.get('request').user
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


class Base64ImageField(serializers.ImageField):
    """
    Кастомное поле для обработки изображений в формате Base64.

    Поддерживает декодирование изображений и сохранение их в файл.
    """

    def to_internal_value(self, data):
        """Декодирует изображение из строки Base64."""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            try:
                img_data = base64.b64decode(imgstr)
            except (TypeError, ValueError):
                raise serializers.ValidationError("Недопустимое изображение.")
            if not imghdr.what(None, img_data):
                raise serializers.ValidationError(
                    "Файл не является изображением.")
            file_name = f"{uuid.uuid4()}.{ext}"
            return ContentFile(img_data, name=file_name)
        return super().to_internal_value(data)


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
