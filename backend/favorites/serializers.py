from rest_framework import serializers
from .models import Favorite
from recipes.models import Recipe
from recipes.serializers import RecipeShortSerializer


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = RecipeShortSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        source='recipe',
        write_only=True
    )

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'recipe', 'recipe_id')
        read_only_fields = ('id', 'user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном.')
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = validated_data['recipe']
        favorite = Favorite.objects.create(user=user, recipe=recipe)
        return favorite
