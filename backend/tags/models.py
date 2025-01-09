from django.db import models

from .constants import TAG_NAME_MAX_LENGTH, TAG_SLUG_MAX_LENGTH


class Tag(models.Model):
    """
    Модель для хранения информации о тегах.

    Атрибуты:
        name: Название тега.
        slug: Уникальный слаг для тега.
    """

    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        verbose_name="Название тега"
    )
    slug = models.SlugField(
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Слаг"
    )

    def __str__(self):
        """Возвращает строковое представление тега."""
        return self.name
