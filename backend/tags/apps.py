"""
Конфигурация приложения Tags.

Этот модуль определяет конфигурацию для приложения Tags.
"""

from django.apps import AppConfig


class TagsConfig(AppConfig):
    """Класс конфигурации для приложения Tags."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tags'
