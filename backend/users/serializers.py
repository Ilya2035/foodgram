import base64
import uuid
import imghdr

from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.files.base import ContentFile

from .models import Profile


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        user = authenticate(username=user.username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        attrs['user'] = user
        return attrs


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar']

    def get_is_subscribed(self, obj):
        # Если подписки реализованы, замените логику
        return False

    def get_avatar(self, obj):
        request = self.context.get('request')
        if hasattr(obj, 'profile') and obj.profile.avatar:
            avatar_url = obj.profile.avatar.url
            return request.build_absolute_uri(avatar_url) if request else avatar_url
        return None


class UserListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar']

    def get_is_subscribed(self, obj):
        # Логика для подписки (если нужно). Пока возвращаем False
        return False

    def get_avatar(self, obj):
        # Добавьте логику для аватара (по умолчанию возвращается заглушка)
        return "http://foodgram.example.org/media/users/default_avatar.png"


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
