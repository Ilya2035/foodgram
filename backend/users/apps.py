"""
Конфигурация приложения Users.

Этот модуль определяет конфигурацию для приложения Users.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Класс конфигурации для приложения Users."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
