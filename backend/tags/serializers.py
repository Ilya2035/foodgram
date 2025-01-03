"""
Сериализаторы для приложения Tags.

Этот модуль содержит сериализатор для работы с моделью Tag.
"""

from rest_framework import serializers
from .models import Tag


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag.

    Используется для представления данных тега в формате JSON.
    """

    class Meta:
        """
        Метаданные для TagSerializer.

        Определяет модель Tag и поля для сериализации.
        """

        model = Tag
        fields = ['id', 'name', 'slug']
