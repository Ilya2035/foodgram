from rest_framework import permissions
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import Tag
from .serializers import TagSerializer


class TagListView(ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class TagDetailView(RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
