"""
Админка для приложения Ingredients.

Этот модуль настраивает отображение модели Ingredient в интерфейсе админки.
"""

from django.contrib import admin
from .models import Ingredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Настройка интерфейса админки для модели Ingredient.

    Включает список отображаемых полей, фильтры и поля для поиска.
    """

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
