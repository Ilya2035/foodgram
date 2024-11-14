from rest_framework import serializers
from .models import ShoppingList
from recipes.models import Recipe
from recipes.serializers import RecipeShortSerializer


class ShoppingListSerializer(serializers.ModelSerializer):
    recipe = RecipeShortSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        source='recipe',
        write_only=True
    )

    class Meta:
        model = ShoppingList
        fields = ('id', 'user', 'recipe', 'recipe_id')
        read_only_fields = ('id', 'user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в списке покупок.')
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = validated_data['recipe']
        shopping_list_item = ShoppingList.objects.create(user=user, recipe=recipe)
        return shopping_list_item
