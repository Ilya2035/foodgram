from django.apps import AppConfig


class IngredientsConfig(AppConfig):
    """
    Конфигурация приложения Ingredients.

    Использует поле BigAutoField в качестве значения по умолчанию
    для автоинкрементных полей.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ingredients'
