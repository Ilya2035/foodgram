"""
Модели для приложения Recipes.

Этот модуль содержит модели для рецептов, ингредиентов, тегов,
избранного и списка покупок.
"""

from django.db import models
from django.contrib.auth.models import User

from tags.models import Tag
from ingredients.models import Ingredient


class Recipe(models.Model):
    """
    Модель для рецепта.

    Хранит данные о названии, тексте рецепта, времени приготовления,
    изображении, авторе, тегах и ингредиентах.
    """

    name = models.CharField(max_length=255)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField()
    image = models.ImageField(upload_to='recipes/images/')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes'
    )

    def get_absolute_url(self):
        """Возвращает абсолютный URL для рецепта."""
        return f"/recipes/{self.id}/"

    class Meta:
        """Метаданные для модели Recipe."""

        ordering = ['-id']

    def __str__(self):
        """Возвращает строковое представление рецепта."""
        return self.name


class RecipeIngredient(models.Model):
    """
    Модель для связи рецептов и ингредиентов.

    Хранит информацию о количестве ингредиента в рецепте.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField()

    class Meta:
        """Метаданные для модели RecipeIngredient."""

        unique_together = ['recipe', 'ingredient']

    def __str__(self):
        """Возвращает строковое представление ингредиента в рецепте."""
        return f"{self.ingredient.name} для {self.recipe.name}"


class ShoppingCart(models.Model):
    """
    Модель для списка покупок.

    Хранит связь между пользователем и рецептами в его списке покупок.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart'
    )

    def __str__(self):
        """Возвращает строковое представление записи в списке покупок."""
        return f"{self.user.username} - {self.recipe.name}"


class Favorite(models.Model):
    """
    Модель для избранных рецептов.

    Хранит связь между пользователем и рецептами в его избранном.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        """Метаданные для модели Favorite."""

        unique_together = ('user', 'recipe')
