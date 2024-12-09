from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework import status, permissions, generics
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from .serializers import (
    UserCreateSerializer,
    UserListRetrieveSerializer,
    SetPasswordSerializer,
    AvatarSerializer
)
from .models import Profile


class UserListView(ListCreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    pagination_class = None  # По необходимости подключите пагинацию

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListRetrieveSerializer


class UserDetailView(RetrieveAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserListRetrieveSerializer
    lookup_field = 'id'


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserListRetrieveSerializer(request.user, context={'request': request})
        return Response(serializer.data)



class UpdateAvatarView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = AvatarSerializer(instance=profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            avatar_url = request.build_absolute_uri(profile.avatar.url)
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            profile = request.user.profile
            if profile.avatar:
                profile.avatar.delete()
            return Response(status=204)
        except Profile.DoesNotExist:
            return Response({"detail": "Профиль не найден."}, status=404)



class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']
            user = request.user
            if not user.check_password(current_password):
                return Response({"current_password": ["Неверный текущий пароль."]}, status=400)
            user.set_password(new_password)
            user.save()
            return Response(status=204)
        return Response(serializer.errors, status=400)



class LoginView(ObtainAuthToken):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        if email is None or password is None:
            return Response({"detail": "Необходимы email и password."}, status=400)
        user = authenticate(username=email, password=password)
        if not user:
            # Если authenticate не прошёл, возможно email не совпадает с username.
            # Если вы используете email как username в authenticate,
            # убедитесь, что соответствие настроено.
            # Либо используйте user = User.objects.filter(email=email).first() и user.check_password.
            user = User.objects.filter(email=email).first()
            if not user or not user.check_password(password):
                return Response({"detail": "Неверные учетные данные."}, status=400)

        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})



class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
        except Token.DoesNotExist:
            pass
        return Response(status=204)
