from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Favorite
from .serializers import FavoriteSerializer
from recipes.models import Recipe
from recipes.serializers import RecipeShortSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        favorite = serializer.save()
        recipe_serializer = RecipeShortSerializer(favorite.recipe, context={'request': request})
        return Response(recipe_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        recipe_id = request.data.get('recipe_id')
        user = request.user
        favorite = Favorite.objects.filter(user=user, recipe__id=recipe_id)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт не найден в избранном.'}, status=status.HTTP_400_BAD_REQUEST)
