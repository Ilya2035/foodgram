"""
Views для приложения Users.

Этот модуль содержит представления для работы с пользователями,
включая регистрацию, авторизацию, изменение пароля, управление аватаром
и подписки.
"""

from rest_framework.views import APIView
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveAPIView,
    ListAPIView
)
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .serializers import (
    UserCreateSerializer,
    UserListRetrieveSerializer,
    SetPasswordSerializer,
    AvatarSerializer,
    UserWithRecipesSerializer
)
from .models import Profile, Subscription
from .pagination import PaginationforUser


class UserListView(ListCreateAPIView):
    """Представление для получения списка пользователей и создания нового."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = PaginationforUser

    def get_serializer_class(self):
        """Возвращает класс сериализатора в зависимости от метода запроса."""
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListRetrieveSerializer


class UserDetailView(RetrieveAPIView):
    """Представление для получения данных о конкретном пользователе."""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserListRetrieveSerializer
    lookup_field = 'id'


class CurrentUserView(APIView):
    """Представление для получения данных о текущем авторизованном."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Возвращает данные о текущем пользователе."""
        serializer = UserListRetrieveSerializer(request.user,
                                                context={'request': request})
        return Response(serializer.data)


class UpdateAvatarView(APIView):
    """Представление для обновления или удаления аватара пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        """Обновляет аватар пользователя."""
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = AvatarSerializer(instance=profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            avatar_url = request.build_absolute_uri(profile.avatar.url)
            return Response({'avatar': avatar_url},
                            status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Удаляет аватар пользователя."""
        try:
            profile = request.user.profile
            if profile.avatar:
                profile.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Profile.DoesNotExist:
            return Response({"detail": "Профиль не найден."},
                            status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    """Представление для изменения пароля пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Изменяет пароль текущего пользователя."""
        serializer = SetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']
            user = request.user

            if not user.check_password(current_password):
                return Response(
                    {"current_password": ["Неверный текущий пароль."]},
                    status=status.HTTP_400_BAD_REQUEST)

            try:
                validate_password(new_password, user=user)
            except ValidationError as e:
                return Response(
                    {"new_password": list(e.messages)},
                    status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(ObtainAuthToken):
    """Представление для аутентификации пользователя и выдачи токена."""

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """Выполняет аутентификацию пользователя и возвращает токен."""
        email = request.data.get('email')
        password = request.data.get('password')
        if email is None or password is None:
            return Response(
                {"detail": "Необходимы email и password."},
                status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=email, password=password)
        if not user:
            user = User.objects.filter(email=email).first()
            if not user or not user.check_password(password):
                return Response(
                    {"detail": "Неверные учетные данные."},
                    status=status.HTTP_400_BAD_REQUEST)

        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


class LogoutView(APIView):
    """Представление для выхода пользователя и удаления токена."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Удаляет токен текущего пользователя."""
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
        except Token.DoesNotExist:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsView(ListAPIView):
    """Представление для получения списка подписок текущего пользователя."""

    serializer_class = UserWithRecipesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PaginationforUser

    def get_queryset(self):
        """Возвращает пользователей, на которых подписан текущий."""
        return User.objects.filter(followers__user=self.request.user)


class SubscribeView(APIView):
    """Представление для подписки и отписки от пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        """Создаёт подписку текущего пользователя на указанного автора."""
        user = request.user
        author = get_object_or_404(User, id=id)

        if user == author:
            return Response({
                "detail": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST)

        if Subscription.objects.filter(user=user, author=author).exists():
            return Response({
                "detail": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST)

        Subscription.objects.create(user=user, author=author)
        serializer = UserWithRecipesSerializer(author,
                                               context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Удаляет подписку текущего пользователя на указанного автора."""
        user = request.user
        author = get_object_or_404(User, id=id)

        subscription = Subscription.objects.filter(user=user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"detail": "Вы не подписаны на этого пользователя."},
            status=status.HTTP_400_BAD_REQUEST)
