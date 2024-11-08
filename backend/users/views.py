from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from djoser.views import UserViewSet as DjoserUserViewSet

from .models import CustomUser, Subscription
from .serializers import CustomUserSerializer, SubscriptionSerializer
from .permissions import IsOwnerOrReadOnly


class CustomUserViewSet(DjoserUserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subscriptions = CustomUser.objects.filter(
            following__user=user
        )
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(subscriptions, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = self.get_object()
        serializer = SubscriptionSerializer(
            author,
            context={'request': request},
        )
        return self.perform_subscribe_action(user, author, serializer)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        user = request.user
        author = self.get_object()
        return self.perform_unsubscribe_action(user, author)

    def perform_subscribe_action(self, user, author, serializer):
        if user == author:
            return Response({'errors': 'Нельзя подписаться на самого себя.'}, status=status.HTTP_400_BAD_REQUEST)
        if Subscription.objects.filter(user=user, author=author).exists():
            return Response({'errors': 'Вы уже подписаны на этого пользователя.'}, status=status.HTTP_400_BAD_REQUEST)
        Subscription.objects.create(user=user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_unsubscribe_action(self, user, author):
        subscription = Subscription.objects.filter(user=user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Вы не подписаны на этого пользователя.'}, status=status.HTTP_400_BAD_REQUEST)
