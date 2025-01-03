"""
Сериализаторы для приложения Ingredients.

Этот модуль содержит сериализатор для модели Ingredient.
"""

from rest_framework import serializers

from .models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Ingredient.

    Преобразует данные ингредиента для API.
    """

    class Meta:
        """
        Метаданные для сериализатора Ingredient.

        Указывает модель и поля, которые будут включены в сериализацию.
        """

        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']
