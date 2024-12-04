from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Recipe, ShoppingCart, Favorite
from .serializers import RecipeSerializer, RecipeSimpleSerializer


class RecipeListCreateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        recipes = Recipe.objects.all()
        serializer = RecipeSerializer(recipes, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RecipeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecipeDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def patch(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            raise PermissionDenied({"detail": "У вас недостаточно прав для изменения данного рецепта."})
        return super().partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            raise PermissionDenied({"detail": "У вас недостаточно прав для удаления данного рецепта."})
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeLinkView(APIView):
    def get(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        # Генерация короткой ссылки (пример, замените на реальную логику)
        short_link = f"https://foodgram.example.org/s/{recipe.id}"
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)


class DownloadShoppingCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Получение списка покупок текущего пользователя
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user)

        if not shopping_cart.exists():
            return Response({"detail": "Список покупок пуст."}, status=400)

        # Формирование контента файла
        content = "Список покупок:\n\n"
        for item in shopping_cart:
            recipe = item.recipe
            content += f"{recipe.name}:\n"
            for ingredient in recipe.ingredients.all():
                content += f" - {ingredient.name} ({ingredient.measurement_unit}): {ingredient.amount}\n"
            content += "\n"

        # Создание HTTP-ответа с файлом
        response = HttpResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response


class ShoppingCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        """Добавление рецепта в список покупок."""
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({"detail": "Рецепт не найден."}, status=status.HTTP_404_NOT_FOUND)

        if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response({"detail": "Рецепт уже в списке покупок."}, status=status.HTTP_400_BAD_REQUEST)

        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeSimpleSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Удаление рецепта из списка покупок."""
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({"detail": "Рецепт не найден."}, status=status.HTTP_404_NOT_FOUND)

        try:
            shopping_cart_item = ShoppingCart.objects.get(user=request.user, recipe=recipe)
            shopping_cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ShoppingCart.DoesNotExist:
            return Response({"detail": "Рецепта нет в списке покупок."}, status=status.HTTP_400_BAD_REQUEST)


class FavoriteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        """Добавление рецепта в избранное."""
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({"detail": "Рецепт не найден."}, status=status.HTTP_404_NOT_FOUND)

        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response({"detail": "Рецепт уже в избранном."}, status=status.HTTP_400_BAD_REQUEST)

        Favorite.objects.create(user=request.user, recipe=recipe)
        serializer = RecipeSimpleSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        """Удаление рецепта из избранного."""
        try:
            recipe = Recipe.objects.get(id=id)
        except Recipe.DoesNotExist:
            return Response({"detail": "Рецепт не найден."}, status=status.HTTP_404_NOT_FOUND)

        try:
            favorite = Favorite.objects.get(user=request.user, recipe=recipe)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Favorite.DoesNotExist:
            return Response({"detail": "Рецепт отсутствует в избранном."}, status=status.HTTP_400_BAD_REQUEST)
