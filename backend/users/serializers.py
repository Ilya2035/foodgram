import base64
import uuid
import imghdr

from django.core.files.base import ContentFile
from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

from .models import Profile, Subscription
from recipes.models import Recipe


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    username = serializers.CharField(
        required=True,
        max_length=128,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message="Никнейм может содержать только буквы, цифры и символы @ . + - _"
            )
        ]
    )
    first_name = serializers.CharField(required=True, max_length=128)
    last_name = serializers.CharField(required=True, max_length=128)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'password']

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

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        # При необходимости создать профиль
        Profile.objects.get_or_create(user=user)
        return user


class UserListRetrieveSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar']

    def get_is_subscribed(self, obj):
        # Логику подписок реализуйте сами, пока False
        return False

    def get_avatar(self, obj):
        request = self.context.get('request')
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return request.build_absolute_uri(obj.profile.avatar.url)
        return None


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            # Отделяем метаданные и контент
            format, imgstr = data.split(';base64,')  # Декодируем строку
            ext = format.split('/')[-1]  # Определяем расширение файла
            # Декодируем содержимое
            try:
                img_data = base64.b64decode(imgstr)
            except (TypeError, ValueError):
                raise serializers.ValidationError("Недопустимое изображение.")
            # Проверяем тип файла
            if not imghdr.what(None, img_data):
                raise serializers.ValidationError("Файл не является изображением.")
            # Создаём уникальное имя для файла
            file_name = f"{uuid.uuid4()}.{ext}"
            return ContentFile(img_data, name=file_name)
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = Profile
        fields = ['avatar']


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class UserWithRecipesSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        ]

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_avatar(self, obj):
        request = self.context.get('request')
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return request.build_absolute_uri(obj.profile.avatar.url)
        return None
