from django.db import models

from .constants import (
    INGREDIENT_NAME_MAX_LENGTH,
    INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH,
)

class Ingredient(models.Model):
    """
    Модель для хранения информации об ингредиентах.

    Содержит название ингредиента и единицу измерения.
    """

    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        verbose_name="Название ингредиента"
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH,
        verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient_name_measurement_unit"
            )
        ]

    def __str__(self):
        """
        Возвращаем более понятное строковое представление.
        """
        return f"{self.name} ({self.measurement_unit})"
