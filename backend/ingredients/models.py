"""
Модели приложения Ingredients.

Этот модуль содержит модель Ingredient для хранения данных о ингредиентах.
"""

from django.db import models


class Ingredient(models.Model):
    """
    Модель для хранения информации об ингредиентах.

    Содержит название ингредиента и единицу измерения.
    """

    name = models.CharField(max_length=255)
    measurement_unit = models.CharField(max_length=50)

    def __str__(self):
        """Возвращает строковое представление ингредиента."""
        return self.name
