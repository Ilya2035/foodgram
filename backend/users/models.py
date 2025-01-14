from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractUser

from .constants import (
    USER_USERNAME_MAX_LENGTH,
    USER_FIRST_NAME_MAX_LENGTH,
    USER_LAST_NAME_MAX_LENGTH
)


class FoodgramUser(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.EmailField(
        verbose_name='Электронная почта',
        unique=True
    )
    username = models.CharField(
        verbose_name='Никнейм',
        max_length=USER_USERNAME_MAX_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Никнейм может содержать только'
                        ' буквы, цифры и символы @ . + - _'
            )
        ]
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=USER_FIRST_NAME_MAX_LENGTH
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=USER_LAST_NAME_MAX_LENGTH
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='avatars/',
        null=True,
        blank=True
    )
    is_staff = models.BooleanField(
        verbose_name='Сотрудник',
        default=False
    )
    date_joined = models.DateTimeField(
        verbose_name='Дата регистрации',
        auto_now_add=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        """Мета класс для модели FoodgramUser."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Возвращает строковое представление пользователя."""
        return self.email


class Subscription(models.Model):
    """
    Модель подписки пользователя.

    user   — подписчик (тот, кто подписывается).
    author — автор, на которого подписываются.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name="Автор"
    )

    class Meta:
        """Мета класс для модели Subscription."""

        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return f"{self.user} подписан на {self.author}"
