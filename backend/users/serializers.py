from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth import authenticate


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
        # Добавьте логику для получения URL аватара, если он есть
        return f"http://foodgram.example.org/media/users/default_avatar.png"


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
