"""
Модели для приложения Tags.

Этот модуль содержит модель Tag для работы с тегами.
"""

from django.db import models


class Tag(models.Model):
    """
    Модель для хранения информации о тегах.

    Атрибуты:
        name: Название тега.
        slug: Уникальный слаг для тега.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        """Возвращает строковое представление тега."""
        return self.name
