from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import ShoppingList
from .serializers import ShoppingListSerializer
from recipes.models import Recipe, Ingredient, RecipeIngredient
from recipes.serializers import RecipeShortSerializer
from django.db.models import Sum
from django.http import HttpResponse


class ShoppingListViewSet(viewsets.ModelViewSet):
    queryset = ShoppingList.objects.all()
    serializer_class = ShoppingListSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        return ShoppingList.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shopping_list_item = serializer.save()
        recipe_serializer = RecipeShortSerializer(shopping_list_item.recipe, context={'request': request})
        return Response(recipe_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        recipe_id = kwargs.get('pk')
        user = request.user
        shopping_list_item = ShoppingList.objects.filter(user=user, recipe__id=recipe_id)
        if shopping_list_item.exists():
            shopping_list_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Рецепт не найден в списке покупок.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_list(self, request):
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_list__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount_total=Sum('amount'))
        shopping_list = 'Список покупок:\n'
        for item in ingredients:
            shopping_list += f"- {item['ingredient__name']}: {item['amount_total']} {item['ingredient__measurement_unit']}\n"
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response
