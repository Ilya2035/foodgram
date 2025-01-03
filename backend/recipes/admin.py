"""
Админка для приложения Recipes.

Этот модуль настраивает отображение моделей Recipe, RecipeIngredient,
ShoppingCart и Favorite в интерфейсе админки.
"""

from django.contrib import admin
from .models import Recipe, RecipeIngredient, ShoppingCart, Favorite


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Настройка интерфейса админки для модели Recipe.

    Отображает основные данные о рецептах с возможностью фильтрации и поиска.
    """

    list_display = ('name', 'author', 'cooking_time')
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('tags', 'cooking_time')
    filter_horizontal = ('tags', 'ingredients')
    readonly_fields = ('get_absolute_url',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """
    Настройка интерфейса админки для модели RecipeIngredient.

    Отображает связи между рецептами и ингредиентами.
    """

    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('ingredient',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """
    Настройка интерфейса админки для модели ShoppingCart.

    Показывает связи пользователей с рецептами в их списках покупок.
    """

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Настройка интерфейса админки для модели Favorite.

    Отображает избранные рецепты пользователей.
    """

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
