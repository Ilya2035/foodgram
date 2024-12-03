from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import Tag
from .serializers import TagSerializer


class TagListView(ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TagDetailView(RetrieveAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
