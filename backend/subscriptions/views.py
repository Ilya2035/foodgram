from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Subscription
from .serializers import SubscriptionSerializer
from users.models import CustomUser

class SubscriptionViewSet(viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscriptionSerializer

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(subscriptions, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def subscribe(self, request, pk=None):
        user = request.user
        author = CustomUser.objects.get(pk=pk)
        if user == author:
            return Response({'errors': 'Нельзя подписаться на самого себя.'}, status=status.HTTP_400_BAD_REQUEST)
        if Subscription.objects.filter(user=user, author=author).exists():
            return Response({'errors': 'Вы уже подписаны на этого автора.'}, status=status.HTTP_400_BAD_REQUEST)
        subscription = Subscription.objects.create(user=user, author=author)
        serializer = self.get_serializer(subscription, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = CustomUser.objects.get(pk=pk)
        subscription = Subscription.objects.filter(user=user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Вы не подписаны на этого автора.'}, status=status.HTTP_400_BAD_REQUEST)

