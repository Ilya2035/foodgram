"""
Конфигурация приложения Recipes.

Этот модуль задаёт конфигурацию для приложения Recipes.
"""

from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """
    Конфигурация приложения Recipes.

    Использует поле BigAutoField в качестве значения по умолчанию
    для автоинкрементных полей.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
