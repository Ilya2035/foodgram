import random
import string

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from tags.models import Tag
from ingredients.models import Ingredient
from .constants import (
    RECIPES_NAME_MAX_LENGTH,
    RECIPES_MIN_COOKING_TIME,
    RECIPES_MAX_COOKING_TIME,
    RECIPES_SHORT_LINK_MAX_LENGT,
    RECIPES_MIN_INGREDIENTS,
    RECIPES_MAX_INGREDIENTS,
)


class Recipe(models.Model):
    """
    Модель для рецепта.

    Хранит данные о названии, тексте рецепта, времени приготовления,
    изображении, авторе, тегах и ингредиентах.
    """

    name = models.CharField(
        max_length=RECIPES_NAME_MAX_LENGTH,
        verbose_name="Название рецепта"
    )
    text = models.TextField(
        verbose_name="Описание рецепта"
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления (в минутах)",
        validators=[
            MinValueValidator(
                RECIPES_MIN_COOKING_TIME,
                message="Время приготовления не может быть меньше 1 минуты."
            ),
            MaxValueValidator(
                RECIPES_MAX_COOKING_TIME,
                message="Время приготовления не может превышать 32000 минут."
            )
        ]
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name="Изображение рецепта"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name="Автор рецепта"
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name="Теги"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name="Ингредиенты"
    )
    short_link = models.CharField(
        max_length=RECIPES_SHORT_LINK_MAX_LENGT,
        unique=True,
        null=True,
        blank=True
    )

    def generate_short_url(self):
        """Генерирует уникальную короткую ссылку."""
        while True:
            short_url = ''.join(
                random.choices(string.ascii_letters + string.digits, k=6))
            if not Recipe.objects.filter(
                    short_link=short_url).exists():
                return short_url

    def save(self, *args, **kwargs):
        """Добавляет генерацию короткой ссылки при создании объекта."""
        if not self.short_link:
            self.short_link = self.generate_short_url()
        super().save(*args, **kwargs)

    class Meta:
        """Метаданные для модели Recipe."""

        ordering = ['name']
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

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
        related_name='recipe_ingredients',
        verbose_name="Рецепт"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент"
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество ингредиента",
        validators=[
            MinValueValidator(
                RECIPES_MIN_INGREDIENTS,
                message="Количество не может быть меньше 1."
            ),
            MaxValueValidator(
                RECIPES_MAX_INGREDIENTS,
                message="Количество не может превышать 32000."
            )
        ]
    )

    class Meta:
        """Метаданные для модели RecipeIngredient."""

        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление ингредиента в рецепте."""
        return f"{self.ingredient.name} для «{self.recipe.name}»"


class UserRecipeBase(models.Model):
    """Абстрактная модель, хранящая связь пользователя и рецепта."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт"
    )

    class Meta:
        """Метаданные для модели UserRecipeBase."""

        abstract = True

    def __str__(self):
        """Возвращает строковое представление ингредиента в рецепте."""
        return f"{self.user.username} — «{self.recipe.name}»"


class ShoppingCart(UserRecipeBase):
    """
    Модель для списка покупок.

    Хранит связь между пользователем и рецептами в его списке покупок.
    """

    class Meta:
        """Метаданные для модели ShoppingCart."""

        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_user_recipe'
            )
        ]


class Favorite(UserRecipeBase):
    """
    Модель для избранных рецептов.

    Хранит связь между пользователем и рецептами в его избранном.
    """

    class Meta:
        """Метаданные для модели Favorite."""

        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_user_recipe'
            )
        ]
